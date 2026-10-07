from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login

LOGIN_REQUIRED_MESSAGE = "Anket oluşturmak için giriş yap ya da hemen üye ol."


def login_required_with_message(view_func=None, message=LOGIN_REQUIRED_MESSAGE):
    """
    Django'nun login_required'ı gibi ziyaretçiyi giriş sayfasına (?next= ile) gönderir,
    ama ek olarak bir bilgi mesajı da bırakır.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view(request, *args, **kwargs)
            messages.info(request, message)
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        return wrapper

    # Hem @login_required_with_message hem @login_required_with_message(message="...") çalışsın
    return decorator(view_func) if view_func else decorator
