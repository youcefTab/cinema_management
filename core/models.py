# core/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductionCompany(models.Model):
    """
    Production company (simplifiée de TMDb production_companies).
    Remplace le model Author.
    """

    tmdb_id = models.BigIntegerField(
        _("TMDb id"), unique=True, null=True, blank=True, db_index=True
    )
    name = models.CharField(_("Nom"), max_length=256)
    logo_path = models.CharField(_("Logo path"), max_length=512, blank=True)
    origin_country = models.CharField(_("Pays d'origine"), max_length=8, blank=True)
    homepage = models.CharField(_("Homepage"), max_length=512, blank=True)

    source = models.CharField(
        _("Source"), max_length=32, default="ADMIN", help_text=_("TMDB or ADMIN")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Production company")
        verbose_name_plural = _("Production companies")

    def __str__(self) -> str:
        return self.name


class Film(models.Model):
    """Film TMDb."""

    tmdb_id = models.BigIntegerField(
        _("TMDb id"), unique=True, null=True, blank=True, db_index=True
    )
    titre = models.CharField(_("Titre"), max_length=512)
    titre_original = models.CharField(_("Titre original"), max_length=512, blank=True)
    overview = models.TextField(_("Résumé / overview"), blank=True)
    release_date = models.DateField(_("Date de sortie"), null=True, blank=True)
    runtime = models.PositiveIntegerField(_("Durée (minutes)"), null=True, blank=True)

    poster_path = models.CharField(_("Poster path"), max_length=512, blank=True)
    backdrop_path = models.CharField(_("Backdrop path"), max_length=512, blank=True)

    vote_average = models.FloatField(_("Note moyenne TMDb"), null=True, blank=True)
    vote_count = models.PositiveIntegerField(
        _("Nombre de votes TMDb"), null=True, blank=True
    )
    popularity = models.FloatField(_("Popularité"), null=True, blank=True)

    original_language = models.CharField(
        _("Langue originale"), max_length=10, blank=True
    )

    adult = models.BooleanField(_("Film adulte"), default=False)
    statut = models.CharField(_("Statut"), max_length=64, default="n/a")

    # relations
    production_companies = models.ManyToManyField(
        ProductionCompany, related_name="films", blank=True
    )

    # provenance flag (TMDB or ADMIN)
    created_via_tmdb = models.BooleanField(
        _("Importé depuis TMDb"), default=False, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tmdb_id"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["created_via_tmdb"]),
        ]
        verbose_name = _("Film")
        verbose_name_plural = _("Films")

    def __str__(self) -> str:
        return f"{self.titre} ({self.release_date or 'n/a'})"


class FilmRating(models.Model):
    """
    Note qu'un spectateur donne à un film (1-5).
    Unique per (spectateur, film).
    """

    spectateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="film_ratings"
    )
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name="ratings")
    value = models.PositiveSmallIntegerField(
        _("Note"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    review = models.TextField(_("Commentaire"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("spectateur", "film")
        ordering = ["-created_at"]
        verbose_name = _("Film rating")
        verbose_name_plural = _("Film ratings")

    def __str__(self) -> str:
        return f"{self.spectateur} -> {self.film}: {self.value}"


class CompanyRating(models.Model):
    """
    Note qu'un spectateur donne a une production company (remplace rating auteur).
    """

    spectateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_ratings",
    )
    company = models.ForeignKey(
        ProductionCompany, on_delete=models.CASCADE, related_name="ratings"
    )
    value = models.PositiveSmallIntegerField(
        _("Note"), choices=[(i, str(i)) for i in range(1, 6)]
    )
    review = models.TextField(_("Commentaire"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("spectateur", "company")
        ordering = ["-created_at"]
        verbose_name = _("Company rating")
        verbose_name_plural = _("Company ratings")

    def __str__(self) -> str:
        return f"{self.spectateur} -> {self.company}: {self.value}"


class Favorite(models.Model):
    """Favoris : association simple spectateur <-> film."""

    spectateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    film = models.ForeignKey(
        Film, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("spectateur", "film")
        ordering = ["-created_at"]
        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")

    def __str__(self) -> str:
        return f"{self.spectateur} x {self.film}"
