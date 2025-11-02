from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from core.models import CompanyRating, Favorite, Film, FilmRating, ProductionCompany

User = get_user_model()


class ProductionCompanyModelTestCase(TestCase):
    """Tests pour le modèle ProductionCompany"""

    def test_create_company(self):
        """Test: Créer une production company"""
        company = ProductionCompany.objects.create(
            name="Warner Bros", tmdb_id=174, origin_country="US", source="TMDB"
        )

        self.assertEqual(company.name, "Warner Bros")
        self.assertEqual(company.tmdb_id, 174)
        self.assertEqual(company.source, "TMDB")
        self.assertIsNotNone(company.created_at)
        self.assertIsNotNone(company.updated_at)

    def test_company_str_representation(self):
        """Test: Représentation string de ProductionCompany"""
        company = ProductionCompany.objects.create(name="Test Studio")
        self.assertEqual(str(company), "Test Studio")

    def test_company_default_source(self):
        """Test: Source par défaut est ADMIN"""
        company = ProductionCompany.objects.create(name="Default Studio")
        self.assertEqual(company.source, "ADMIN")

    def test_company_unique_tmdb_id(self):
        """Test: tmdb_id doit être unique"""
        ProductionCompany.objects.create(name="Company 1", tmdb_id=123)

        with self.assertRaises(IntegrityError):
            ProductionCompany.objects.create(name="Company 2", tmdb_id=123)

    def test_company_ordering(self):
        """Test: Les companies sont ordonnées par nom"""
        ProductionCompany.objects.create(name="Zulu Films")
        ProductionCompany.objects.create(name="Alpha Studio")

        companies = list(ProductionCompany.objects.all())
        self.assertEqual(companies[0].name, "Alpha Studio")
        self.assertEqual(companies[1].name, "Zulu Films")

    def test_company_optional_fields(self):
        """Test: Les champs optionnels peuvent être vides"""
        company = ProductionCompany.objects.create(name="Minimal Studio")

        self.assertEqual(company.logo_path, "")
        self.assertEqual(company.origin_country, "")
        self.assertEqual(company.homepage, "")
        self.assertIsNone(company.tmdb_id)


class FilmModelTestCase(TestCase):
    """Tests pour le modèle Film"""

    def setUp(self):
        self.company = ProductionCompany.objects.create(name="Test Studio")

    def test_create_film(self):
        """Test: Créer un film"""
        film = Film.objects.create(
            titre="Inception",
            titre_original="Inception",
            overview="A movie about dreams",
            release_date=date(2010, 7, 16),
            runtime=148,
            statut="published",
            tmdb_id=27205,
        )

        self.assertEqual(film.titre, "Inception")
        self.assertEqual(film.runtime, 148)
        self.assertFalse(film.created_via_tmdb)  # Default
        self.assertIsNotNone(film.created_at)

    def test_film_str_representation(self):
        """Test: Représentation string de Film"""
        film = Film.objects.create(titre="Test Film", release_date=date(2020, 1, 1))
        self.assertEqual(str(film), "Test Film (2020-01-01)")

    def test_film_str_without_release_date(self):
        """Test: String representation sans date de sortie"""
        film = Film.objects.create(titre="Film Sans Date")
        self.assertEqual(str(film), "Film Sans Date (n/a)")

    def test_film_default_values(self):
        """Test: Valeurs par défaut du film"""
        film = Film.objects.create(titre="Default Film")

        self.assertEqual(film.statut, "n/a")
        self.assertFalse(film.adult)
        self.assertFalse(film.created_via_tmdb)

    def test_film_production_companies_relation(self):
        """Test: Relation ManyToMany avec production companies"""
        film = Film.objects.create(titre="Test Film")
        company1 = ProductionCompany.objects.create(name="Company 1")
        company2 = ProductionCompany.objects.create(name="Company 2")

        film.production_companies.add(company1, company2)

        self.assertEqual(film.production_companies.count(), 2)
        self.assertIn(company1, film.production_companies.all())
        self.assertIn(company2, film.production_companies.all())

    def test_film_unique_tmdb_id(self):
        """Test: tmdb_id doit être unique"""
        Film.objects.create(titre="Film 1", tmdb_id=123)

        with self.assertRaises(IntegrityError):
            Film.objects.create(titre="Film 2", tmdb_id=123)

    def test_film_ordering(self):
        """Test: Les films sont ordonnés par created_at décroissant"""
        film1 = Film.objects.create(titre="Old Film")
        film2 = Film.objects.create(titre="New Film")

        films = list(Film.objects.all())
        self.assertEqual(films[0], film2)  # Plus récent en premier
        self.assertEqual(films[1], film1)

    def test_film_optional_fields(self):
        """Test: Les champs optionnels peuvent être vides"""
        film = Film.objects.create(titre="Minimal Film")

        self.assertEqual(film.titre_original, "")
        self.assertEqual(film.overview, "")
        self.assertIsNone(film.release_date)
        self.assertIsNone(film.runtime)


class FilmRatingModelTestCase(TestCase):
    """Tests pour le modèle FilmRating"""

    def setUp(self):
        self.user = User.objects.create_user(username="spectateur1", password="pass123")
        self.film = Film.objects.create(titre="Test Film")

    def test_create_film_rating(self):
        """Test: Créer une note de film"""
        rating = FilmRating.objects.create(
            spectateur=self.user, film=self.film, value=5, review="Excellent film!"
        )

        self.assertEqual(rating.value, 5)
        self.assertEqual(rating.review, "Excellent film!")
        self.assertEqual(rating.spectateur, self.user)
        self.assertEqual(rating.film, self.film)

    def test_film_rating_str_representation(self):
        """Test: Représentation string de FilmRating"""
        rating = FilmRating.objects.create(
            spectateur=self.user, film=self.film, value=4
        )
        expected = f"{self.user} -> {self.film}: 4"
        self.assertEqual(str(rating), expected)

    def test_film_rating_unique_together(self):
        """Test: Un spectateur ne peut noter qu'une fois le même film"""
        FilmRating.objects.create(spectateur=self.user, film=self.film, value=5)

        with self.assertRaises(IntegrityError):
            FilmRating.objects.create(spectateur=self.user, film=self.film, value=3)

    def test_film_rating_ordering(self):
        """Test: Les notes sont ordonnées par created_at décroissant"""
        FilmRating.objects.create(spectateur=self.user, film=self.film, value=3)

        film2 = Film.objects.create(titre="Film 2")
        rating2 = FilmRating.objects.create(spectateur=self.user, film=film2, value=5)

        ratings = list(FilmRating.objects.all())
        self.assertEqual(ratings[0], rating2)  # Plus récent en premier

    def test_film_rating_optional_review(self):
        """Test: Le commentaire est optionnel"""
        rating = FilmRating.objects.create(
            spectateur=self.user, film=self.film, value=4
        )
        self.assertEqual(rating.review, "")

    def test_film_rating_cascade_delete_user(self):
        """Test: Supprimer un user supprime ses notes"""
        FilmRating.objects.create(spectateur=self.user, film=self.film, value=5)

        self.assertEqual(FilmRating.objects.count(), 1)
        self.user.delete()
        self.assertEqual(FilmRating.objects.count(), 0)

    def test_film_rating_cascade_delete_film(self):
        """Test: Supprimer un film supprime ses notes"""
        FilmRating.objects.create(spectateur=self.user, film=self.film, value=5)

        self.assertEqual(FilmRating.objects.count(), 1)
        self.film.delete()
        self.assertEqual(FilmRating.objects.count(), 0)


class CompanyRatingModelTestCase(TestCase):
    """Tests pour le modèle CompanyRating"""

    def setUp(self):
        self.user = User.objects.create_user(username="spectateur1", password="pass123")
        self.company = ProductionCompany.objects.create(name="Test Company")

    def test_create_company_rating(self):
        """Test: Créer une note de company"""
        rating = CompanyRating.objects.create(
            spectateur=self.user, company=self.company, value=4, review="Bon studio"
        )

        self.assertEqual(rating.value, 4)
        self.assertEqual(rating.review, "Bon studio")

    def test_company_rating_str_representation(self):
        """Test: Représentation string de CompanyRating"""
        rating = CompanyRating.objects.create(
            spectateur=self.user, company=self.company, value=5
        )
        expected = f"{self.user} -> {self.company}: 5"
        self.assertEqual(str(rating), expected)

    def test_company_rating_unique_together(self):
        """Test: Un spectateur ne peut noter qu'une fois la même company"""
        CompanyRating.objects.create(
            spectateur=self.user, company=self.company, value=5
        )

        with self.assertRaises(IntegrityError):
            CompanyRating.objects.create(
                spectateur=self.user, company=self.company, value=3
            )

    def test_company_rating_cascade_delete(self):
        """Test: Cascade delete fonctionne"""
        CompanyRating.objects.create(
            spectateur=self.user, company=self.company, value=5
        )

        self.assertEqual(CompanyRating.objects.count(), 1)
        self.company.delete()
        self.assertEqual(CompanyRating.objects.count(), 0)


class FavoriteModelTestCase(TestCase):
    """Tests pour le modèle Favorite"""

    def setUp(self):
        self.user = User.objects.create_user(username="spectateur1", password="pass123")
        self.film = Film.objects.create(titre="Test Film")

    def test_create_favorite(self):
        """Test: Créer un favori"""
        favorite = Favorite.objects.create(spectateur=self.user, film=self.film)

        self.assertEqual(favorite.spectateur, self.user)
        self.assertEqual(favorite.film, self.film)
        self.assertIsNotNone(favorite.created_at)

    def test_favorite_str_representation(self):
        """Test: Représentation string de Favorite"""
        favorite = Favorite.objects.create(spectateur=self.user, film=self.film)
        expected = f"{self.user} x {self.film}"
        self.assertEqual(str(favorite), expected)

    def test_favorite_unique_together(self):
        """Test: Un spectateur ne peut ajouter qu'une fois le même film"""
        Favorite.objects.create(spectateur=self.user, film=self.film)

        with self.assertRaises(IntegrityError):
            Favorite.objects.create(spectateur=self.user, film=self.film)

    def test_favorite_ordering(self):
        """Test: Les favoris sont ordonnés par created_at décroissant"""
        Favorite.objects.create(spectateur=self.user, film=self.film)

        film2 = Film.objects.create(titre="Film 2")
        fav2 = Favorite.objects.create(spectateur=self.user, film=film2)

        favorites = list(Favorite.objects.all())
        self.assertEqual(favorites[0], fav2)  # Plus récent en premier

    def test_favorite_cascade_delete_user(self):
        """Test: Supprimer un user supprime ses favoris"""
        Favorite.objects.create(spectateur=self.user, film=self.film)

        self.assertEqual(Favorite.objects.count(), 1)
        self.user.delete()
        self.assertEqual(Favorite.objects.count(), 0)

    def test_favorite_cascade_delete_film(self):
        """Test: Supprimer un film supprime les favoris associés"""
        Favorite.objects.create(spectateur=self.user, film=self.film)

        self.assertEqual(Favorite.objects.count(), 1)
        self.film.delete()
        self.assertEqual(Favorite.objects.count(), 0)

    def test_multiple_users_same_film_favorite(self):
        """Test: Plusieurs users peuvent avoir le même film en favori"""
        user2 = User.objects.create_user(username="spectateur2", password="pass123")

        Favorite.objects.create(spectateur=self.user, film=self.film)
        Favorite.objects.create(spectateur=user2, film=self.film)

        self.assertEqual(Favorite.objects.count(), 2)
        self.assertEqual(self.film.favorited_by.count(), 2)
