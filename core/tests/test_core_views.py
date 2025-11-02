from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import CompanyRating, Favorite, Film, FilmRating, ProductionCompany

User = get_user_model()


class ProductionCompanyViewSetTestCase(TestCase):
    """Tests pour ProductionCompanyViewSet"""

    def setUp(self):
        """Configuration initiale pour chaque test"""

        self.client = APIClient()

        # Nettoyer la DB avant chaque test
        ProductionCompany.objects.all().delete()
        Film.objects.all().delete()
        User.objects.all().delete()

        # Créer un utilisateur spectateur
        self.user = User.objects.create_user(
            username="spectateur1", email="spectateur@test.com", password="testpass123"
        )

        # Créer des production companies
        self.company1 = ProductionCompany.objects.create(
            name="Warner Bros", tmdb_id=174, source="TMDB", origin_country="US"
        )

        self.company2 = ProductionCompany.objects.create(
            name="Studio Test", source="ADMIN", origin_country="FR"
        )

        # URLs
        self.list_url = "/api/companies/"
        self.detail_url = lambda pk: f"/api/companies/{pk}/"
        self.rate_url = lambda pk: f"/api/companies/{pk}/rate/"

    def test_list_companies_public(self):
        """Test: Lister les companies (accès public)"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_by_source(self):
        """Test: Filtrer les companies par source"""
        # Companies ADMIN
        response = self.client.get(f"{self.list_url}?source=ADMIN")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["source"], "ADMIN")

        # Companies TMDB
        response = self.client.get(f"{self.list_url}?source=TMDB")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["source"], "TMDB")

    def test_retrieve_company_public(self):
        """Test: Récupérer une company (accès public)"""
        response = self.client.get(self.detail_url(self.company1.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Warner Bros")
        self.assertEqual(response.data["tmdb_id"], 174)

    def test_create_company_requires_auth(self):
        """Test: Créer une company nécessite authentification"""
        data = {"name": "New Studio", "origin_country": "UK"}

        # Sans auth - devrait échouer
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Avec auth - devrait réussir
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductionCompany.objects.count(), 3)

    def test_update_company(self):
        """Test: Modifier une company"""
        self.client.force_authenticate(user=self.user)
        data = {"name": "Warner Bros Updated"}

        response = self.client.patch(
            self.detail_url(self.company1.pk), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.company1.refresh_from_db()
        self.assertEqual(self.company1.name, "Warner Bros Updated")

    def test_delete_company_without_films(self):
        """Test: Supprimer une company sans films"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url(self.company2.pk))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ProductionCompany.objects.count(), 1)

    def test_delete_company_with_films_fails(self):
        """Test: Impossible de supprimer une company avec des films"""
        self.client.force_authenticate(user=self.user)

        # Créer un film associé
        film = Film.objects.create(titre="Test Film", statut="published")
        film.production_companies.add(self.company1)

        response = self.client.delete(self.detail_url(self.company1.pk))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(ProductionCompany.objects.count(), 2)

    def test_rate_company_authenticated(self):
        """Test: Noter une company (authentifié)"""
        self.client.force_authenticate(user=self.user)

        data = {"value": 5, "review": "Excellent studio!"}
        response = self.client.post(
            self.rate_url(self.company1.pk), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["value"], 5)
        self.assertEqual(CompanyRating.objects.count(), 1)

    def test_rate_company_unauthenticated_fails(self):
        """Test: Noter une company sans authentification échoue"""
        data = {"value": 5}
        response = self.client.post(
            self.rate_url(self.company1.pk), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_existing_rating(self):
        """Test: Mettre à jour une note existante"""
        self.client.force_authenticate(user=self.user)

        # Première note
        CompanyRating.objects.create(
            spectateur=self.user, company=self.company1, value=3, review="Moyen"
        )

        # Nouvelle note (update)
        data = {"value": 5, "review": "Finalement excellent!"}
        response = self.client.post(
            self.rate_url(self.company1.pk), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CompanyRating.objects.count(), 1)

        rating = CompanyRating.objects.first()
        self.assertEqual(rating.value, 5)
        self.assertEqual(rating.review, "Finalement excellent!")

    def test_rate_company_invalid_value(self):
        """Test: Noter avec une valeur invalide"""
        self.client.force_authenticate(user=self.user)

        data = {"value": 6}  # Invalide (max 5)
        response = self.client.post(
            self.rate_url(self.company1.pk), data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pagination(self):
        """Test: Pagination fonctionne"""
        # Créer 15 companies supplémentaires
        for i in range(13):
            ProductionCompany.objects.create(name=f"Company {i}")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertEqual(len(response.data["results"]), 10)  # page_size=10

    def test_custom_page_size(self):
        """Test: Taille de page personnalisée"""
        for i in range(5):
            ProductionCompany.objects.create(name=f"Company Extra {i}")

        response = self.client.get(f"{self.list_url}?page_size=3")
        self.assertEqual(len(response.data["results"]), 3)


class FilmViewSetTestCase(TestCase):
    """Tests pour FilmViewSet"""

    def setUp(self):
        """Configuration initiale"""
        self.client = APIClient()

        # Nettoyer la DB
        Film.objects.all().delete()
        ProductionCompany.objects.all().delete()
        User.objects.all().delete()

        self.user = User.objects.create_user(
            username="spectateur1", email="spectateur@test.com", password="testpass123"
        )

        self.company = ProductionCompany.objects.create(name="Warner Bros", tmdb_id=174)

        # Films de test
        self.film1 = Film.objects.create(
            titre="Inception",
            titre_original="Inception",
            overview="Un film sur les rêves",
            release_date=date(2010, 7, 16),
            statut="published",
            created_via_tmdb=True,
            tmdb_id=27205,
        )
        self.film1.production_companies.add(self.company)

        self.film2 = Film.objects.create(
            titre="Film Admin", statut="draft", created_via_tmdb=False
        )

        # URLs
        self.list_url = "/api/films/"
        self.detail_url = lambda pk: f"/api/films/{pk}/"
        self.rate_url = lambda pk: f"/api/films/{pk}/rate/"
        self.favorite_url = lambda pk: f"/api/films/{pk}/favorite/"
        self.my_favorites_url = "/api/films/my-favorites/"
        self.archive_url = lambda pk: f"/api/films/{pk}/archive/"

    def test_list_films_public(self):
        """Test: Lister les films (accès public)"""
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_by_statut(self):
        """Test: Filtrer les films par statut"""
        response = self.client.get(f"{self.list_url}?statut=published")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["statut"], "published")
        self.assertEqual(response.data["results"][0]["titre"], "Inception")

    def test_filter_by_created_via_tmdb(self):
        """Test: Filtrer par source (TMDb ou Admin)"""
        # Films TMDb
        response = self.client.get(f"{self.list_url}?created_via_tmdb=true")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertTrue(response.data["results"][0]["created_via_tmdb"])

        # Films Admin
        response = self.client.get(f"{self.list_url}?created_via_tmdb=false")
        self.assertEqual(len(response.data["results"]), 1)
        self.assertFalse(response.data["results"][0]["created_via_tmdb"])

    def test_retrieve_film_public(self):
        """Test: Récupérer un film (accès public)"""
        response = self.client.get(self.detail_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["titre"], "Inception")
        self.assertIn("production_companies", response.data)

    def test_create_film_requires_auth(self):
        """Test: Créer un film nécessite authentification"""
        data = {"titre": "New Film", "statut": "draft"}

        # Sans auth
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Avec auth
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_film_requires_auth(self):
        """Test: Modifier un film nécessite authentification"""
        data = {"titre": "Inception Updated"}

        # Sans auth
        response = self.client.patch(
            self.detail_url(self.film1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Avec auth
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.detail_url(self.film1.pk), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rate_film_authenticated(self):
        """Test: Noter un film"""
        self.client.force_authenticate(user=self.user)

        data = {"value": 5, "review": "Chef d'œuvre absolu!"}
        response = self.client.post(self.rate_url(self.film1.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["value"], 5)
        self.assertEqual(FilmRating.objects.count(), 1)

    def test_update_film_rating(self):
        """Test: Mettre à jour une note de film existante"""
        self.client.force_authenticate(user=self.user)

        # Première note
        FilmRating.objects.create(spectateur=self.user, film=self.film1, value=3)

        # Update
        data = {"value": 5, "review": "Encore mieux!"}
        response = self.client.post(self.rate_url(self.film1.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FilmRating.objects.count(), 1)

        rating = FilmRating.objects.first()
        self.assertEqual(rating.value, 5)

    def test_rate_film_unauthenticated_fails(self):
        """Test: Noter sans authentification échoue"""
        data = {"value": 5}
        response = self.client.post(self.rate_url(self.film1.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_favorite(self):
        """Test: Ajouter un film aux favoris"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.favorite_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertTrue(
            Favorite.objects.filter(spectateur=self.user, film=self.film1).exists()
        )

    def test_add_favorite_twice_returns_200(self):
        """Test: Ajouter deux fois le même favori retourne 200"""
        self.client.force_authenticate(user=self.user)

        # Premier ajout
        response1 = self.client.post(self.favorite_url(self.film1.pk))
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Deuxième ajout
        response2 = self.client.post(self.favorite_url(self.film1.pk))
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_remove_favorite(self):
        """Test: Retirer un film des favoris"""
        self.client.force_authenticate(user=self.user)

        # Ajouter d'abord
        Favorite.objects.create(spectateur=self.user, film=self.film1)

        # Retirer
        response = self.client.delete(self.favorite_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_remove_nonexistent_favorite(self):
        """Test: Retirer un favori inexistant retourne 404"""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.favorite_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_my_favorites(self):
        """Test: Lister mes films favoris"""
        self.client.force_authenticate(user=self.user)

        # Ajouter des favoris
        Favorite.objects.create(spectateur=self.user, film=self.film1)
        Favorite.objects.create(spectateur=self.user, film=self.film2)

        response = self.client.get(self.my_favorites_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_my_favorites_unauthenticated_fails(self):
        """Test: Lister favoris sans authentification échoue"""
        response = self.client.get(self.my_favorites_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_archive_film(self):
        """Test: Archiver un film"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.archive_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.film1.refresh_from_db()
        self.assertEqual(self.film1.statut, "archived")

    def test_archive_film_unauthenticated_fails(self):
        """Test: Archiver sans authentification échoue"""
        response = self.client.post(self.archive_url(self.film1.pk))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_pagination_films(self):
        """Test: Pagination des films"""
        # Créer 13 films supplémentaires
        for i in range(13):
            Film.objects.create(titre=f"Film {i}", statut="published")

        response = self.client.get(self.list_url)

        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)

    def test_filter_adult_content(self):
        """Test: Filtrer le contenu adulte"""
        # Nettoyer et créer un film adult uniquement
        Film.objects.all().delete()
        Film.objects.create(titre="Film Adult", adult=True, statut="published")

        response = self.client.get(f"{self.list_url}?adult=true")

        self.assertEqual(len(response.data["results"]), 1)
        self.assertTrue(response.data["results"][0]["adult"])

    def test_film_with_multiple_companies(self):
        """Test: Film avec plusieurs production companies"""
        company2 = ProductionCompany.objects.create(name="Universal")
        self.film1.production_companies.add(company2)

        response = self.client.get(self.detail_url(self.film1.pk))

        self.assertEqual(len(response.data["production_companies"]), 2)


class EdgeCasesTestCase(TestCase):
    """Tests de cas limites et erreurs"""

    def setUp(self):
        self.client = APIClient()
        User.objects.all().delete()
        Film.objects.all().delete()

        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_rate_with_invalid_value_zero(self):
        """Test: Noter avec 0 (invalide)"""
        self.client.force_authenticate(user=self.user)
        film = Film.objects.create(titre="Test Film")

        data = {"value": 0}
        response = self.client.post(f"/api/films/{film.pk}/rate/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_nonexistent_film(self):
        """Test: Noter un film inexistant"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/films/99999/rate/", {"value": 5}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_company(self):
        """Test: Supprimer une company inexistante"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete("/api/companies/99999/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_film_rating_without_review(self):
        """Test: Noter un film sans commentaire (optionnel)"""
        self.client.force_authenticate(user=self.user)
        film = Film.objects.create(titre="Test")

        response = self.client.post(
            f"/api/films/{film.pk}/rate/", {"value": 4}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rating = FilmRating.objects.first()
        self.assertEqual(rating.review, "")


class PermissionsTestCase(TestCase):
    """Tests des permissions"""

    def setUp(self):
        self.client = APIClient()
        User.objects.all().delete()
        Film.objects.all().delete()
        ProductionCompany.objects.all().delete()

        self.user = User.objects.create_user(username="user1", password="pass123")
        self.film = Film.objects.create(titre="Test Film")
        self.company = ProductionCompany.objects.create(name="Test Company")

    def test_public_can_list_films(self):
        """Test: Utilisateurs non authentifiés peuvent lister les films"""
        response = self.client.get("/api/films/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_can_retrieve_film(self):
        """Test: Utilisateurs non authentifiés peuvent voir un film"""
        response = self.client.get(f"/api/films/{self.film.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_cannot_create_film(self):
        """Test: Utilisateurs non authentifiés ne peuvent pas créer de film"""
        response = self.client.post("/api/films/", {"titre": "New Film"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_create_film(self):
        """Test: Utilisateurs authentifiés peuvent créer des films"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/films/", {"titre": "New Film", "statut": "draft"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_public_can_list_companies(self):
        """Test: Lecture publique des companies"""
        response = self.client.get("/api/companies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_cannot_create_company(self):
        """Test: Création de company nécessite authentification"""
        response = self.client.post(
            "/api/companies/", {"name": "New Company"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
