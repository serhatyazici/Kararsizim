from django import template
from django.utils import timezone
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def time_ago(value):
    """Tek birimlik göreli zaman: "5 dakika önce", "2 saat önce"."""
    if not value:
        return ""
    if (timezone.now() - value).total_seconds() < 60:
        return "az önce"
    return f"{timesince(value, depth=1)} önce"


@register.filter
def avatar_color(username):
    """Kullanıcı adından türetilen sabit renk numarası (1–5 → --opt-1 … --opt-5)."""
    return sum(ord(char) for char in str(username)) % 5 + 1
