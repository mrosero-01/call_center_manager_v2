from django.contrib.auth import views as auth_views
from django.core.cache import cache

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_SECONDS = 300


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "unknown")


def _login_rate_key(request):
    return f"login-rate:{_get_client_ip(request)}"


class RateLimitedLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            attempts = cache.get(
                _login_rate_key(request),
                0,
            )

            if attempts >= LOGIN_RATE_LIMIT:
                form = self.get_form()
                form.add_error(
                    None,
                    (
                        "Demasiados intentos de inicio de sesión. "
                        "Espera unos minutos e inténtalo de nuevo."
                    ),
                )

                return self.form_invalid(form)

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def form_invalid(self, form):
        cache_key = _login_rate_key(self.request)

        if cache.add(
            cache_key,
            1,
            LOGIN_RATE_WINDOW_SECONDS,
        ):
            return super().form_invalid(form)

        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(
                cache_key,
                1,
                LOGIN_RATE_WINDOW_SECONDS,
            )

        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(
            _login_rate_key(self.request),
        )

        return super().form_valid(form)
