from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

# Kullanıcı adı olarak alınamayacak, sistemde özel anlamı olan kelimeler
RESERVED_USERNAMES = {
    "admin", "root", "kararsizim", "destek", "support",
    "anket", "giris", "kayit", "cikis",
}

username_format_validator = RegexValidator(
    regex=r"^[a-z0-9_.]{3,20}$",
    message="Kullanıcı adı 3–20 karakter olmalı; küçük harf, rakam, _ ve . kullanabilirsin.",
)


def validate_username_not_reserved(value):
    if value.lower() in RESERVED_USERNAMES:
        raise ValidationError("Bu kullanıcı adı kullanılamaz.")


class UserManager(BaseUserManager):
    """
    Manager = modelin "sorgu kapısı" (User.objects). Burada kullanıcı oluşturma
    işini e-posta ile giriş yapacak şekilde özelleştiriyoruz.
    """

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("E-posta zorunludur.")
        if not username:
            raise ValueError("Kullanıcı adı zorunludur.")
        user = self.model(
            email=self.normalize_email(email).lower(),
            username=username.lower(),
            **extra_fields,
        )
        user.set_password(password)  # parola şifrelenerek (hash) saklanır
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser için is_staff=True olmalı.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser için is_superuser=True olmalı.")
        return self._create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField("e-posta", unique=True)
    username = models.CharField(
        "kullanıcı adı",
        max_length=20,
        unique=True,
        validators=[username_format_validator, validate_username_not_reserved],
        error_messages={"unique": "Bu kullanıcı adı zaten alınmış."},
    )

    USERNAME_FIELD = "email"  # giriş kimliği e-posta
    REQUIRED_FIELDS = ["username"]  # createsuperuser'ın ayrıca soracağı alanlar

    objects = UserManager()

    class Meta:
        verbose_name = "kullanıcı"
        verbose_name_plural = "kullanıcılar"
        constraints = [
            # Büyük/küçük harf duyarsız benzersizlik: veritabanı düzeyinde güvence
            models.UniqueConstraint(Lower("email"), name="unique_email_ci"),
            models.UniqueConstraint(Lower("username"), name="unique_username_ci"),
        ]

    def save(self, *args, **kwargs):
        # E-posta ve kullanıcı adı her zaman küçük harfle saklanır
        self.email = self.email.lower()
        self.username = self.username.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"@{self.username}"
