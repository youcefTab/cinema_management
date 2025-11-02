from unittest.mock import MagicMock, patch

import httpx
import pytest

from core.tmdb_integration.exceptions import TMDBClientError
from core.tmdb_integration.tmdb_client import TMDBClient


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("TMDB_API_TOKEN", "fake-token")
    monkeypatch.setenv("TMDB_BASE_URL", "https://fake.tmdb.org/3")


@pytest.fixture
def client(mock_env):
    """Return a TMDBClient instance with mocked environment."""
    return TMDBClient()


def test_close_success(client):
    """Should close the client without errors."""
    client.client.close = MagicMock()
    client.close()
    client.client.close.assert_called_once()


def test_close_with_exception(client, caplog):
    """Should log exception if closing fails."""
    client.client.close = MagicMock(side_effect=Exception("Boom"))
    client.close()
    assert "Erreur lors de la fermeture" in caplog.text


@patch("core.tmdb_integration.tmdb_client.httpx.Client.get")
def test___get_success(mock_get, client):
    """Should return JSON data on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    data = client._TMDBClient__get("/movie/popular")
    assert data == {"ok": True}
    mock_get.assert_called_once()


@patch("core.tmdb_integration.tmdb_client.httpx.Client.get")
def test___get_network_error(mock_get, client):
    """Should raise TMDBClientError on network issue."""
    mock_get.side_effect = httpx.RequestError("network down")
    with pytest.raises(TMDBClientError, match="Erreur de connexion"):
        client._TMDBClient__get("/movie/popular")


@patch("core.tmdb_integration.tmdb_client.httpx.Client.get")
def test___get_http_error(mock_get, client):
    """Should raise TMDBClientError on 404."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    http_error = httpx.HTTPStatusError("error", request=None, response=mock_response)
    mock_get.side_effect = http_error

    with pytest.raises(TMDBClientError, match="Erreur HTTP TMDb: 404"):
        client._TMDBClient__get("/movie/popular")


@patch.object(TMDBClient, "_TMDBClient__get")
def test_get_popular_movies(mock_get, client):
    """Should iterate pages and combine results."""
    mock_get.side_effect = [
        {"results": [{"id": 1}]},
        {"results": [{"id": 2}]},
    ]
    movies = client.get_popular_movies(page_count=2)
    assert movies == [{"id": 1}, {"id": 2}]
    assert mock_get.call_count == 2


@patch.object(TMDBClient, "_TMDBClient__get")
def test_get_movie_details_success(mock_get, client):
    """Should return movie details when found."""
    mock_get.return_value = {"id": 100, "title": "Matrix"}
    movie = client.get_movie_details(100)
    assert movie["title"] == "Matrix"
    mock_get.assert_called_once_with("/movie/100")


@patch.object(TMDBClient, "_TMDBClient__get")
def test_get_movie_details_not_found(mock_get, client):
    """Should return None if 404 error."""
    mock_get.side_effect = TMDBClientError("Erreur HTTP TMDb: 404")
    result = client.get_movie_details(123)
    assert result is None


@patch.object(TMDBClient, "_TMDBClient__get")
def test_get_movie_details_other_error(mock_get, client):
    """Should re-raise TMDBClientError if not 404."""
    mock_get.side_effect = TMDBClientError("Erreur HTTP TMDb: 500")
    with pytest.raises(TMDBClientError):
        client.get_movie_details(123)
