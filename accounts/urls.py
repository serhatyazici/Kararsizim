from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("kayit/", views.signup, name="signup"),
    path("giris/", views.KararsizimLoginView.as_view(), name="login"),
    path("cikis/", views.KararsizimLogoutView.as_view(), name="logout"),
]
