from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models


class Poll(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="polls",
        verbose_name="yazar",
    )
    question = models.CharField("soru", max_length=200)
    description = models.TextField("açıklama", max_length=500, blank=True)
    created_at = models.DateTimeField("oluşturulma", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "anket"
        verbose_name_plural = "anketler"

    def __str__(self):
        return self.question


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="anket",
    )
    text = models.CharField("metin", max_length=80)
    # 0–4 arası: hem sırayı hem de seçeneğin rengini (--opt-1 … --opt-5) belirler
    position = models.PositiveSmallIntegerField(
        "sıra", validators=[MaxValueValidator(4)]
    )

    class Meta:
        ordering = ["position"]
        verbose_name = "seçenek"
        verbose_name_plural = "seçenekler"
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "position"], name="unique_option_position_per_poll"
            ),
        ]

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="votes",  # benzersizlik kısıtı için anketle de ilişkili tutulur
        verbose_name="anket",
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="seçenek",
    )
    # Giriş yapılmışsa oyu veren üye; üye silinirse oy kalır (SET_NULL)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes",
        verbose_name="kullanıcı",
    )
    # Tarayıcı çerezinden gelen anonim kimlik (ziyaretçiler de oy verebilsin diye)
    voter_token = models.UUIDField("oy veren tarayıcı")
    created_at = models.DateTimeField("oluşturulma", auto_now_add=True)

    class Meta:
        verbose_name = "oy"
        verbose_name_plural = "oylar"
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "voter_token"], name="one_vote_per_browser"
            ),
            models.UniqueConstraint(
                fields=["poll", "user"],
                condition=models.Q(user__isnull=False),
                name="one_vote_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.poll_id} → {self.option_id}"
