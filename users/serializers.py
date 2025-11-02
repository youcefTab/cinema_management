from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from rest_framework import serializers

from .models import Spectateur

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "bio", "avatar", "date_naissance")

    def validate_email(self, value: str) -> str:
        """Ensure the email is unique."""

        validate_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        """Create a new user with the validated data."""

        user = User.objects.create_user(**validated_data)
        return user


class SpectateurSerializer(serializers.ModelSerializer):
    """Serializer for retrieving and updating spectator profile."""

    class Meta:
        model = Spectateur
        fields = ("username", "email", "bio", "avatar", "date_naissance")
        read_only_fields = ("username", "email")
