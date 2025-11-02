from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import (
    CompanyRating,
    Favorite,
    Film,
    FilmRating,
    ProductionCompany,
)


class ProductionCompanySerializer(serializers.ModelSerializer):
    """Serializer lisible pour ProductionCompany (read)."""

    class Meta:
        model = ProductionCompany
        fields = [
            "id",
            "tmdb_id",
            "name",
            "logo_path",
            "origin_country",
            "homepage",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "source"]


class ProductionCompanyWriteSerializer(serializers.ModelSerializer):
    """Serializer pour écriture (create/update) d'une company."""

    class Meta:
        model = ProductionCompany
        fields = [
            "tmdb_id",
            "name",
            "logo_path",
            "origin_country",
            "homepage",
        ]


class FilmSerializer(serializers.ModelSerializer):
    """
    Serializer principal pour Film.
    - en lecture : on expose les companies via ProductionCompanySerializer (nested)
    - en écriture : on accepte `production_companies_ids` (list d'ids) pour établir la M2M
    """

    production_companies = ProductionCompanySerializer(many=True, read_only=True)
    production_companies_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProductionCompany.objects.all(),
        write_only=True,
        required=False,
        source="production_companies",
        help_text="Liste d'ids de production companies (pour écriture)",
    )

    class Meta:
        model = Film
        fields = [
            "id",
            "tmdb_id",
            "titre",
            "titre_original",
            "overview",
            "release_date",
            "runtime",
            "poster_path",
            "backdrop_path",
            "vote_average",
            "vote_count",
            "popularity",
            "original_language",
            "adult",
            "statut",
            "production_companies",
            "production_companies_ids",
            "created_via_tmdb",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "production_companies"]

    def create(self, validated_data: dict[str, Any]) -> Film:
        companies = validated_data.pop("production_companies", [])
        film = super().create(validated_data)
        if companies:
            film.production_companies.set(companies)
        return film

    def update(self, instance: Film, validated_data: dict[str, Any]) -> Film:
        companies = validated_data.pop("production_companies", None)
        film = super().update(instance, validated_data)
        if companies is not None:
            film.production_companies.set(companies)
        return film


class FilmRatingSerializer(serializers.ModelSerializer):
    """Serializer pour créer / afficher une note de film."""

    spectateur = serializers.StringRelatedField(read_only=True)  # type: ignore
    film = serializers.PrimaryKeyRelatedField(
        queryset=Film.objects.all(), required=False
    )

    class Meta:
        model = FilmRating
        fields = [
            "id",
            "spectateur",
            "film",
            "value",
            "review",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "spectateur", "created_at", "updated_at"]


class CompanyRatingSerializer(serializers.ModelSerializer):
    """Serializer pour créer / afficher une note de production company."""

    spectateur = serializers.StringRelatedField(read_only=True)  # type: ignore
    company = serializers.PrimaryKeyRelatedField(
        queryset=ProductionCompany.objects.all(), required=False
    )

    class Meta:
        model = CompanyRating
        fields = ["id", "spectateur", "company", "value", "review", "created_at"]
        read_only_fields = ["id", "spectateur", "created_at"]


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer pour lier un favorit — lecture seule utile pour list endpoints."""

    spectateur = serializers.StringRelatedField(read_only=True)  # type: ignore
    film = FilmSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "spectateur", "film", "created_at"]
        read_only_fields = ["id", "spectateur", "film", "created_at"]
