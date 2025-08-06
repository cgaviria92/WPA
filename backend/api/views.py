from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from .models import PlayerProfile
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        PlayerProfile.objects.create(user=user)  # experiencia=0, coint=100 por defecto
        return Response({"message": "User created"}, status=status.HTTP_201_CREATED)

class PlayerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile = PlayerProfile.objects.get(user=request.user)
        return Response({
            "username": request.user.username,
            "experiencia": profile.experiencia,
            "coint": profile.coint
        })
