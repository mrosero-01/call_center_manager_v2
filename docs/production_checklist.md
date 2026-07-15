# Checklist de producción

## Configuración

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` largo, aleatorio y privado.
- `DJANGO_ALLOWED_HOSTS=dominio.example.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://dominio.example.com`
- `DJANGO_SECURE_SSL_REDIRECT=True` si Django gestiona la redirección HTTPS.
- `DJANGO_SESSION_COOKIE_SECURE=True`
- `DJANGO_CSRF_COOKIE_SECURE=True`
- `DJANGO_SECURE_HSTS_SECONDS=31536000` solo cuando HTTPS esté confirmado.
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True` solo si todos los subdominios usan HTTPS.
- `DJANGO_SECURE_HSTS_PRELOAD=True` solo si se desea entrar al preload list.

## Comandos previos

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py test accounts callcenters schedules
.venv/bin/python manage.py collectstatic --noinput
```

## Prueba manual

- Iniciar sesión con usuario normal.
- Confirmar que solo ve sus call centers.
- Iniciar sesión con superuser.
- Confirmar que ve todos los call centers.
- Abrir un call center y cambiar un horario.
- Confirmar que pide motivo obligatorio.
- Confirmar que se crea el historial.
- Confirmar que el día seleccionado se mantiene después de guardar.
- Consultar la vista legacy usada por Asterisk:
  `/horario/{codename}/{Day}`
- Verificar que devuelve los intervalos correctos.

## Asterisk

- No cambiar dialplan en este release sin prueba controlada.
- Confirmar que ODBC sigue apuntando a la vista PostgreSQL esperada.
- Confirmar comportamiento para día cerrado y día con varios intervalos.
