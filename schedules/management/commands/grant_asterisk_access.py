import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


ROLE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
ASTERISK_VIEWS = (
    "schedules_asterisk_callcenter_status",
)


class Command(BaseCommand):
    help = "Concede acceso de solo lectura a las vistas usadas por Asterisk."

    def add_arguments(self, parser):
        parser.add_argument("--role", required=True)

    def handle(self, *args, **options):
        role = options["role"]

        if not ROLE_PATTERN.fullmatch(role):
            raise CommandError(
                "El rol solo puede contener minúsculas, números y guiones bajos."
            )

        if connection.vendor != "postgresql":
            raise CommandError("Este comando requiere PostgreSQL.")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s",
                [role],
            )

            if cursor.fetchone() is None:
                raise CommandError(
                    f"El rol PostgreSQL {role} no existe."
                )

            quoted_role = connection.ops.quote_name(role)

            for view_name in ASTERISK_VIEWS:
                quoted_view = connection.ops.quote_name(view_name)
                cursor.execute(
                    f"GRANT SELECT ON {quoted_view} TO {quoted_role}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Acceso de solo lectura concedido a {role}."
            )
        )
