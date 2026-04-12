from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CLINICIAN = 'clinician', 'Clinician'
        PATIENT = 'patient', 'Patient'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.PATIENT)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
