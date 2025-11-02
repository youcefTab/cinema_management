from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Spectateur(AbstractUser):
    """Custom user model representing a cinema spectator."""

    bio = models.TextField(_("Biography"), blank=True, null=True)
    avatar = models.URLField(_("Avatar URL"), blank=True, null=True)
    date_naissance = models.DateField(_("Date de naissance"), blank=True, null=True)

    class Meta:
        verbose_name = "Spectateur"
        verbose_name_plural = "Spectateurs"

    def __str__(self) -> str:
        return self.username
