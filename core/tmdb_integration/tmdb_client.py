import logging
from typing import Any

import environ
import httpx

from .exceptions import TMDBClientError

env = environ.Env()
logger = logging.getLogger(__name__)

TMDB_API_TOKEN = env.str("TMDB_API_TOKEN", "")
TMDB_BASE_URL = env.str("TMDB_BASE_URL", "https://api.themoviedb.org/3")


class TMDBClient:
    """Client asynchrone pour interagir avec l'API TMDb."""

    def __init__(self):
        """Initialise le client TMDb avec la clé API et la configuration HTTP."""

        self.api_key = TMDB_API_TOKEN
        if not self.api_key:
            raise TMDBClientError(
                "TMDB_API_TOKEN non défini dans l'environnement ou les settings Django."
            )

        self.client = httpx.Client(
            base_url=TMDB_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(10.0),
        )

    def close(self):
        """Ferme le client HTTP."""

        try:
            self.client.close()
        except Exception:
            logger.exception("Erreur lors de la fermeture du client TMDb")

    def __get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Méthode interne générique pour exécuter une requête GET TMDb."""

        if params is None:
            params = {}
        params.setdefault("language", "en-US")

        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
        except httpx.RequestError as e:
            logger.error("Erreur réseau TMDb: %s", e)
            raise TMDBClientError("Erreur de connexion à TMDb") from e
        except httpx.HTTPStatusError as e:
            logger.error(
                "Erreur HTTP TMDb (%s): %s", e.response.status_code, e.response.text
            )
            raise TMDBClientError(f"Erreur HTTP TMDb: {e.response.status_code}") from e

        return response.json()

    def get_popular_movies(self, page_count: int = 1) -> list[dict[str, Any]]:
        """
        Récupère les films populaires sur plusieurs pages.
        Exemple : client.get_popular_movies(page_count=3)
        """
        all_movies: list[dict[str, Any]] = []

        for page in range(1, page_count + 1):
            logger.info("Fetching TMDb popular movies page %d...", page)
            data = self.__get("/movie/popular", params={"page": page})
            results = data.get("results", [])
            all_movies.extend(results)

        return all_movies

    def get_movie_details(self, tmdb_id: int) -> dict[str, Any] | None:
        """
        Récupère les détails d'un film spécifique.
        Retourne None si le film est introuvable (404).
        """

        try:
            data = self.__get(f"/movie/{tmdb_id}")
        except TMDBClientError as e:
            if "404" in str(e):
                return None
            raise
        return data
