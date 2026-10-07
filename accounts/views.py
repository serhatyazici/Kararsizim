from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, SignupForm


def get_safe_next_url(request):
    """
    ?next= değerini okur; sadece bizim sitemize giden adresleri kabul eder.
    (Aksi halde saldırgan, girişten sonra kullanıcıyı kendi sitesine yönlendirebilir: "open redirect".)
    """
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    is_safe = url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )
    return next_url if is_safe else ""


def signup(request):
    # View = isteği (request) alıp yanıt (response) döndüren fonksiyon
    if request.user.is_authenticated:
        return redirect("/")

    next_url = get_safe_next_url(request)
    form = SignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)  # kayıttan sonra otomatik giriş
        messages.success(request, f"Hoş geldin @{user.username}! 🎉")
        return redirect(next_url or "/")

    return render(request, "accounts/signup.html", {"form": form, "next": next_url})


class KararsizimLoginView(LoginView):
    # LoginView: Django'nun hazır giriş view'ı. ?next= güvenlik kontrolünü de kendisi yapar.
    authentication_form = LoginForm
    template_name = "accounts/login.html"


class KararsizimLogoutView(LogoutView):
    # Django 5'te çıkış yalnızca POST ile çalışır (GET ile çıkış CSRF'e açıktır).
    pass
