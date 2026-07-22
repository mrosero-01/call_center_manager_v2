import hashlib

from django.contrib.auth import views as auth_views
from django.core.cache import cache

from config.request_utils import get_client_ip

LOGIN_RATE_WINDOW_SECONDS = 300
LOGIN_PAIR_RATE_LIMIT = 5
LOGIN_USERNAME_RATE_LIMIT = 10
LOGIN_IP_RATE_LIMIT = 30


def _normalized_username(request):
    return request.POST.get("username", "").strip().casefold()


def _username_digest(request):
    return hashlib.sha256(
        _normalized_username(request).encode("utf-8"),
    ).hexdigest()


def _login_rate_keys(request):
    ip_address = get_client_ip(request)
    username_digest = _username_digest(request)

    return (
        (f"login-rate:pair:{ip_address}:{username_digest}", LOGIN_PAIR_RATE_LIMIT),
        (f"login-rate:user:{username_digest}", LOGIN_USERNAME_RATE_LIMIT),
        (f"login-rate:ip:{ip_address}", LOGIN_IP_RATE_LIMIT),
    )


def _increment_rate_key(cache_key):
    if cache.add(cache_key, 1, LOGIN_RATE_WINDOW_SECONDS):
        return

    try:
        cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, LOGIN_RATE_WINDOW_SECONDS)


class RateLimitedLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "placeholder": "Usuario",
            }
        )
        form.fields["password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
                "placeholder": "Contraseña",
            }
        )

        return form

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            rate_limited = any(
                cache.get(cache_key, 0) >= limit
                for cache_key, limit in _login_rate_keys(request)
            )

            if rate_limited:
                form = self.get_form()
                form.add_error(
                    None,
                    (
                        "Demasiados intentos de inicio de sesión. "
                        "Espera unos minutos e inténtalo de nuevo."
                    ),
                )
                form.rate_limited = True

                response = self.render_to_response(
                    self.get_context_data(form=form),
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(
                    LOGIN_RATE_WINDOW_SECONDS,
                )
                return response

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def form_invalid(self, form):
        for cache_key, _limit in _login_rate_keys(self.request):
            _increment_rate_key(cache_key)

        return super().form_invalid(form)

    def form_valid(self, form):
        rate_keys = _login_rate_keys(self.request)
        cache.delete_many(
            [
                rate_keys[0][0],
                rate_keys[1][0],
            ]
        )

        return super().form_valid(form)
