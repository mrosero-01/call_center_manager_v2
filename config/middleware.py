class SecurityHeadersMiddleware:
    """Add browser restrictions not currently managed by SecurityMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault(
            "Permissions-Policy",
            (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=()"
            ),
        )
        return response
