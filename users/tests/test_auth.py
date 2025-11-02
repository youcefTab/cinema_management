import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
    def make_user(**kwargs):
        data = {
            "username": "youz",
            "email": "youz@example.com",
            "password": "StrongPass123!",
        }
        data.update(kwargs)
        return User.objects.create_user(**data)

    return make_user


# ---------------------------
# REGISTER TESTS
# ---------------------------


def test_register_success(api_client):
    url = reverse("register")
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "StrongPass123!",
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "user" in response.data
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["username"] == "newuser"


def test_register_existing_email(api_client, create_user):
    create_user(email="dup@example.com", username="existing")
    url = reverse("register")
    data = {
        "username": "newuser",
        "email": "dup@example.com",
        "password": "StrongPass123!",
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


def test_register_invalid_email(api_client):
    url = reverse("register")
    data = {
        "username": "invalidemail",
        "email": "notanemail",
        "password": "StrongPass123!",
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


def test_register_weak_password(api_client):
    url = reverse("register")
    data = {
        "username": "weakpass",
        "email": "weakpass@example.com",
        "password": "123",
    }

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data


# ---------------------------
# LOGIN TESTS
# ---------------------------


def test_login_success(api_client, create_user):
    user = create_user()
    url = reverse("login")
    data = {"username": user.username, "password": "StrongPass123!"}

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_invalid_credentials(api_client, create_user):
    user = create_user()
    url = reverse("login")
    data = {"username": user.username, "password": "WrongPassword"}

    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------
# TOKEN REFRESH TESTS
# ---------------------------


def test_refresh_token_success(api_client, create_user):
    user = create_user()
    refresh = str(RefreshToken.for_user(user))
    url = reverse("token_refresh")

    response = api_client.post(url, {"refresh": refresh}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


def test_refresh_token_invalid(api_client):
    url = reverse("token_refresh")
    response = api_client.post(url, {"refresh": "invalidtoken"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------
# LOGOUT TESTS
# ---------------------------


def test_logout_success(api_client, create_user):
    user = create_user()
    refresh = str(RefreshToken.for_user(user))
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    url = reverse("logout")
    response = api_client.post(url, {"refresh": refresh}, format="json")

    assert response.status_code == status.HTTP_205_RESET_CONTENT
    assert response.data["message"] == "Déconnexion réussie."


def test_logout_missing_token(api_client, create_user):
    user = create_user()
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    url = reverse("logout")
    response = api_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Refresh token required."


def test_logout_invalid_token(api_client, create_user):
    user = create_user()
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    url = reverse("logout")
    response = api_client.post(url, {"refresh": "invalidtoken"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Token invalide ou expiré."


# ---------------------------
# PROFILE TESTS
# ---------------------------


def test_get_profile_success(api_client, create_user):
    user = create_user()
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    url = reverse("profile")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == user.username


def test_update_profile_success(api_client, create_user):
    user = create_user()
    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    url = reverse("profile")
    data = {"bio": "Je suis un grand fan de cinéma."}
    response = api_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["bio"] == "Je suis un grand fan de cinéma."


def test_update_profile_unauthorized(api_client):
    url = reverse("profile")
    data = {"bio": "Tentative sans token."}
    response = api_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
