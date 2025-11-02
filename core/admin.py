from __future__ import annotations

from django.contrib import admin

from .models import CompanyRating, Favorite, Film, FilmRating, ProductionCompany


@admin.register(ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tmdb_id", "origin_country", "source", "created_at")
    search_fields = ("name", "tmdb_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titre",
        "tmdb_id",
        "release_date",
        "vote_average",
        "statut",
        "created_via_tmdb",
        "created_at",
    )
    list_filter = ("statut", "created_via_tmdb", "adult", "created_at")
    search_fields = ("titre", "tmdb_id", "titre_original")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("production_companies",)


@admin.register(FilmRating)
class FilmRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "spectateur", "film", "value", "created_at")
    search_fields = ("spectateur__username", "film__titre")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CompanyRating)
class CompanyRatingAdmin(admin.ModelAdmin):
    list_display = ("id", "spectateur", "company", "value", "created_at")
    search_fields = ("spectateur__username", "company__name")
    readonly_fields = ("created_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "spectateur", "film", "created_at")
    search_fields = ("spectateur__username", "film__titre")
    readonly_fields = ("created_at",)
