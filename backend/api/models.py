from django.db import models
from django.contrib.auth.models import User

class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    experiencia = models.IntegerField(default=0)
    coint = models.IntegerField(default=100)

    def __str__(self):
        return self.user.username
