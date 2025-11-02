"""
Filtres personnalisés pour l'API Cinema
"""

import django_filters

from .models import Film, ProductionCompany


class FilmFilter(django_filters.FilterSet):
    """
    Filtres pour les films

    Usage:
    - ?statut=published
    - ?statut=archived
    - ?created_via_tmdb=true
    - ?created_via_tmdb=false
    - ?adult=true
    - ?adult=false
    """

    statut = django_filters.CharFilter(
        field_name="statut",
        lookup_expr="iexact",
        help_text="Filtrer par statut (published, draft, archived, etc.)",
    )

    created_via_tmdb = django_filters.BooleanFilter(
        field_name="created_via_tmdb",
        help_text="true = Films TMDb, false = Films Admin",
    )

    adult = django_filters.BooleanFilter(
        field_name="adult", help_text="true = Contenu adulte uniquement"
    )

    class Meta:
        model = Film
        fields = ["statut", "created_via_tmdb", "adult"]


class ProductionCompanyFilter(django_filters.FilterSet):
    """
    Filtres pour les production companies

    Usage:
    - ?source=ADMIN
    - ?source=TMDB
    """

    source = django_filters.CharFilter(
        field_name="source",
        lookup_expr="iexact",
        help_text="Filtrer par source (ADMIN ou TMDB)",
    )

    class Meta:
        model = ProductionCompany
        fields = ["source"]
