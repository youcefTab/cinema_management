from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Spectateur


@admin.register(Spectateur)
class SpectateurAdmin(UserAdmin):
    """Admin configuration for Spectateur."""

    model = Spectateur
    list_display = ("username", "email", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (  # type: ignore
        (
            "Informations supplémentaires",
            {"fields": ("bio", "avatar", "date_naissance")},
        ),
    )
