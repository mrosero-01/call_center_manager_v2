from django.contrib.auth import views as auth_views
from django.core.cache import cache

from config.request_utils import get_client_ip

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_SECONDS = 300


def _login_rate_key(request):
    return f"login-rate:{get_client_ip(request)}"


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
                form.rate_limited = True

                return self.render_to_response(
                    self.get_context_data(form=form),
                )

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
