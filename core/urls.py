# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FilmViewSet, ProductionCompanyViewSet

router = DefaultRouter()
router.register(r"films", FilmViewSet, basename="film")
router.register(r"companies", ProductionCompanyViewSet, basename="company")

urlpatterns = [
    path("", include(router.urls)),
]
