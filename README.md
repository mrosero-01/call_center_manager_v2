# Siptic Manager

Aplicación Django para administrar clientes, CallCenters, usuarios, horarios,
audios de cierre y auditoría. Asterisk consulta PostgreSQL mediante ODBC con un
usuario de solo lectura.

## Requisitos de desarrollo

- Python 3.13
- PostgreSQL 17
- SoX para preparar audios de Asterisk
- Un entorno virtual de Python

## Configuración local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.development.example .env
# Editar las credenciales PostgreSQL de .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

`runserver` se usa únicamente para desarrollo. El empaquetado de producción se
incorporará en la siguiente fase.

## Pruebas PostgreSQL

Crear una base separada cuyo propietario sea el usuario de la aplicación y
configurar `DB_TEST_NAME`:

```bash
sudo -u postgres createdb --owner=callcenter_app test_callcenter_manager
DB_TEST_NAME=test_callcenter_manager \
  .venv/bin/python manage.py test --keepdb
```

## Integración con Asterisk

La vista `schedules_asterisk_callcenter_status` calcula en PostgreSQL:

- Estado activo del cliente y CallCenter.
- Apertura en la zona horaria configurada.
- Audio de cierre.
- Zona horaria aplicada.

Después de crear un rol PostgreSQL de solo lectura:

```bash
.venv/bin/python manage.py grant_asterisk_access \
  --role asterisk_schedule_reader
```

Los ejemplos de `func_odbc` y dialplan se encuentran en `asterisk/`. Los WAV
deben instalarse en:

```text
/var/lib/asterisk/sounds/custom/callcenter_manager/
```

Consulta también `docs/audio_assets.md` y `docs/production_checklist.md`.

## Despliegue

La instalación limpia con Docker, Apache en un puerto dedicado y Asterisk
existente está documentada paso a paso en `docs/deployment.md`. Los comandos
principales son:

```bash
./deploy/scripts/init-env.sh empresa.com 4000
./deploy/scripts/install.sh
sudo ./deploy/apache/configure.sh --apply
sudo ./asterisk/integrate.sh --check
```
