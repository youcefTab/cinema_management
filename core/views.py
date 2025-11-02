from __future__ import annotations

from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import FilmFilter, ProductionCompanyFilter
from .models import CompanyRating, Favorite, Film, FilmRating, ProductionCompany
from .serializers import (
    CompanyRatingSerializer,
    FavoriteSerializer,
    FilmRatingSerializer,
    FilmSerializer,
    ProductionCompanySerializer,
    ProductionCompanyWriteSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination standard avec taille de page configurable via query param `page_size`."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductionCompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour ProductionCompany (remplace Auteur).

    Endpoints:
    - GET    /companies/          : Liste des companies
    - GET    /companies/{id}/     : Détail d'une company
    - POST   /companies/          : Créer une company
    - PUT    /companies/{id}/     : Modifier une company
    - PATCH  /companies/{id}/     : Modifier partiellement
    - DELETE /companies/{id}/     : Supprimer (si pas de films)
    - POST   /companies/{id}/rate/: Noter une company

    Filtres:
    - ?source=ADMIN : Companies créées depuis l'admin
    - ?source=TMDB  : Companies importées depuis TMDb

    Permissions:
    - Lecture: Publique
    - Écriture: Authentification requise
    """

    queryset = ProductionCompany.objects.all().order_by("name")
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]  # Lecture publique, écriture auth

    # Configuration des filtres
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductionCompanyFilter
    search_fields = ["name", "origin_country"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        """Serializer différent selon l'action"""
        if self.action in ("create", "update", "partial_update"):
            return ProductionCompanyWriteSerializer
        return ProductionCompanySerializer

    def destroy(self, request, *args, **kwargs):
        """Supprime une company seulement si elle n'a pas de films associés"""
        obj: ProductionCompany = self.get_object()
        if obj.films.exists():
            raise ValidationError(
                {"error": "Cannot delete company with associated films."}
            )
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="rate",
    )
    def rate(self, request, pk: int | None = None) -> Response:
        """
        Note une production company (ou met à jour la note existante).

        Body:
        {
            "value": 1-5,
            "review": "Commentaire optionnel"
        }
        """
        company = self.get_object()
        serializer = CompanyRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        defaults = {
            "value": serializer.validated_data["value"],
            "review": serializer.validated_data.get("review", ""),
        }

        # Update or create
        obj, created = CompanyRating.objects.update_or_create(
            spectateur=request.user, company=company, defaults=defaults
        )

        out_serializer = CompanyRatingSerializer(obj)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out_serializer.data, status=status_code)


class FilmViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour Film.

    Endpoints:
    - GET    /films/                : Liste des films
    - GET    /films/{id}/           : Détail d'un film
    - POST   /films/                : Créer un film
    - PUT    /films/{id}/           : Modifier un film
    - PATCH  /films/{id}/           : Modifier partiellement
    - POST   /films/{id}/rate/      : Noter un film
    - POST   /films/{id}/favorite/  : Ajouter aux favoris
    - DELETE /films/{id}/favorite/  : Retirer des favoris
    - GET    /films/my-favorites/   : Mes films favoris
    - POST   /films/{id}/archive/   : Archiver un film

    Filtres:
    - ?statut=published         : Films publiés
    - ?statut=archived          : Films archivés
    - ?created_via_tmdb=true    : Films importés de TMDb
    - ?created_via_tmdb=false   : Films créés depuis l'admin
    - ?adult=true               : Contenu adulte

    Permissions:
    - Lecture: Publique
    - Écriture: Authentification requise
    """

    queryset = (
        Film.objects.all()
        .prefetch_related("production_companies")
        .order_by("-created_at")
    )
    serializer_class = FilmSerializer
    pagination_class = StandardResultsSetPagination

    # Configuration des filtres - CRITIQUE pour le cahier des charges
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = FilmFilter
    search_fields = ["titre", "titre_original", "overview"]
    ordering_fields = ["created_at", "release_date", "vote_average", "popularity"]

    def get_permissions(self):
        """Lecture publique, actions mutatives nécessitent l'authentification"""
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="rate",
    )
    def rate(self, request, pk: int | None = None) -> Response:
        """
        Note un film (ou met à jour la note existante).

        Body:
        {
            "value": 1-5,
            "review": "Commentaire optionnel"
        }
        """
        film = self.get_object()
        serializer = FilmRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        defaults = {
            "value": serializer.validated_data["value"],
            "review": serializer.validated_data.get("review", ""),
        }

        obj, created = FilmRating.objects.update_or_create(
            spectateur=request.user, film=film, defaults=defaults
        )

        out_serializer = FilmRatingSerializer(obj)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out_serializer.data, status=status_code)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="favorite",
    )
    def add_favorite(self, request, pk: int | None = None) -> Response:
        """Ajoute un film aux favoris du spectateur"""
        film = self.get_object()
        try:
            fav, created = Favorite.objects.get_or_create(
                spectateur=request.user, film=film
            )
        except IntegrityError as err:
            raise ValidationError({"error": "Unable to create favorite."}) from err

        serializer = FavoriteSerializer(fav)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @add_favorite.mapping.delete
    def remove_favorite(self, request, pk: int | None = None) -> Response:
        """Retire un film des favoris du spectateur"""
        film = self.get_object()
        deleted, _ = Favorite.objects.filter(
            spectateur=request.user, film=film
        ).delete()

        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Favorite not found."}, status=status.HTTP_404_NOT_FOUND
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="my-favorites",
    )
    def my_favorites(self, request) -> Response:
        """Liste les films favoris du spectateur connecté"""
        fav_qs = (
            Favorite.objects.filter(spectateur=request.user)
            .select_related("film")
            .order_by("-created_at")
        )

        films = Film.objects.filter(
            id__in=fav_qs.values_list("film_id", flat=True)
        ).prefetch_related("production_companies")

        page = self.paginate_queryset(films)
        if page is not None:
            serializer = FilmSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = FilmSerializer(films, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="archive",
    )
    def archive(self, request, pk: int | None = None) -> Response:
        """Archive un film (change le statut à 'archived')"""
        film = self.get_object()
        film.statut = "archived"
        film.save(update_fields=["statut", "updated_at"])
        return Response({"detail": "Film archived."}, status=status.HTTP_200_OK)
