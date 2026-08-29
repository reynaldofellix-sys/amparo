from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class AgeGroup(models.TextChoices):
        YOUNG = "young", "Até 24 anos"
        ADULT = "adult", "25 a 59 anos"
        SENIOR = "senior", "60 anos ou mais"
        UNSPECIFIED = "unspecified", "Prefiro não informar"

    username = None
    email = models.EmailField("e-mail", unique=True)
    full_name = models.CharField("nome completo", max_length=180)
    phone = models.CharField("telefone", max_length=20)
    age_group = models.CharField(
        "faixa etária", max_length=20, choices=AgeGroup.choices, default=AgeGroup.UNSPECIFIED
    )
    large_text = models.BooleanField("texto ampliado", default=False)
    transfer_alerts = models.BooleanField(default=True)
    login_alerts = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    confirm_transfers = models.BooleanField(default=True)
    onboarding_completed = models.BooleanField("cadastro completo", default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
    objects = UserManager()

    class Meta:
        ordering = ["full_name", "email"]

    def __str__(self):
        return self.full_name or self.email

    def get_full_name(self):
        return self.full_name

    @property
    def first_name_display(self):
        return self.full_name.split()[0] if self.full_name else "Usuário"
