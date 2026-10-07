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
