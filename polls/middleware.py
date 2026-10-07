import uuid

from django.conf import settings

COOKIE_NAME = "kz_voter"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 yıl


def parse_token(raw):
    """Çerez değeri geçerli bir UUID ise döndürür, değilse None."""
    try:
        return uuid.UUID(raw)
    except (TypeError, ValueError, AttributeError):
        return None


class VoterTokenMiddleware:
    """
    Middleware = her isteğin view'a ulaşmadan önce ve yanıt dönerken geçtiği ara katman.

    Her tarayıcıya anonim bir kimlik (kz_voter çerezi) verir; böylece üye olmayan
    ziyaretçiler de "anket başına 1 oy" kuralına tabi olabilir. View'lar kimliği
    request.voter_token olarak okur.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = parse_token(request.COOKIES.get(COOKIE_NAME))
        is_new = token is None
        if is_new:
            token = uuid.uuid4()
        request.voter_token = token

        response = self.get_response(request)

        if is_new:
            response.set_cookie(
                COOKIE_NAME,
                str(token),
                max_age=COOKIE_MAX_AGE,
                httponly=True,  # JavaScript okuyamaz
                samesite="Lax",
                secure=not settings.DEBUG,  # production'da sadece HTTPS
            )
        return response
