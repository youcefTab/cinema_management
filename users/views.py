from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, SpectateurSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new spectator."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle user registration."""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": RegisterSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve and update the profile of the authenticated spectator."""

    serializer_class = SpectateurSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the authenticated user."""

        return self.request.user


class LogoutView(APIView):
    """Blacklist the provided refresh token (logout)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Handle user logout by blacklisting the refresh token."""

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"error": "Token invalide ou expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT
        )
