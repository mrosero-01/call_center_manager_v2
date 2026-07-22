from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.shortcuts import render


@require_GET
@never_cache
def healthcheck(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {"status": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok"})


def permission_denied(request, exception=None):
    return render(
        request,
        "errors/403.html",
        status=403,
    )


def page_not_found(request, exception=None):
    return render(
        request,
        "errors/404.html",
        status=404,
    )
