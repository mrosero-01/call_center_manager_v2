# Despliegue limpio con Docker y Asterisk existente

Esta guía asume que Apache y Asterisk ya existen en el servidor. Docker solo
administra Django y una base PostgreSQL nueva.

## Puertos

| Puerto | Alcance | Uso |
| --- | --- | --- |
| `4000` | Red/Internet | Apache HTTPS para usuarios |
| `14000` | Solo `127.0.0.1` | Apache hacia Gunicorn |
| `55432` | Solo `127.0.0.1` | Asterisk hacia PostgreSQL Docker |

Los valores son configurables. PostgreSQL y Gunicorn nunca deben publicarse en
`0.0.0.0`.

## 1. Requisitos

```bash
docker --version
docker compose version
apache2ctl -M
asterisk -rx "core show version"
```

Instala Docker Engine y el complemento Compose siguiendo la guía oficial para
la distribución del servidor: `https://docs.docker.com/engine/install/`.

En Debian, la integración ODBC requiere normalmente:

```bash
sudo apt update
sudo apt install unixodbc odbc-postgresql
```

También se necesitan los módulos Apache `ssl`, `proxy`, `proxy_http` y
`headers`, un certificado válido para el dominio y el driver ODBC PostgreSQL.

## 2. Crear configuración

```bash
./deploy/scripts/init-env.sh empresa.com 4000
nano deploy/.env.production
./deploy/scripts/check.sh
```

El archivo se crea con permisos `600` y secretos aleatorios. Copia el valor de
`ASTERISK_DB_PASSWORD` posteriormente a `asterisk/.env`.

## 3. Levantar base y aplicación

```bash
./deploy/scripts/install.sh
./deploy/scripts/status.sh
```

La primera ejecución crea una base vacía, aplica todas las migraciones, crea
las vistas telefónicas y solicita el primer superusuario.

No uses `docker compose down --volumes`: eliminaría la base persistente.

## 4. Configurar Apache

Ajusta en `deploy/.env.production` las rutas reales del certificado y ejecuta:

```bash
sudo -E SIPTIC_ENV_FILE="$PWD/deploy/.env.production" \
  ./deploy/apache/configure.sh --check
sudo -E SIPTIC_ENV_FILE="$PWD/deploy/.env.production" \
  ./deploy/apache/configure.sh --dry-run
sudo -E SIPTIC_ENV_FILE="$PWD/deploy/.env.production" \
  ./deploy/apache/configure.sh --apply
```

Abre el puerto configurado en el firewall y prueba:

```bash
curl -I https://empresa.com:4000/health/
```

Por ejemplo, si el servidor utiliza UFW:

```bash
sudo ufw allow 4000/tcp
```

La web existente puede enlazar a `https://empresa.com:4000/`.

## 5. Integrar sin reemplazar Asterisk

```bash
cp asterisk/.env.example asterisk/.env
chmod 600 asterisk/.env
nano asterisk/.env
sudo -E SIPTIC_ASTERISK_ENV="$PWD/asterisk/.env" \
  ./asterisk/integrate.sh --check
sudo -E SIPTIC_ASTERISK_ENV="$PWD/asterisk/.env" \
  ./asterisk/integrate.sh --dry-run
```

Después de revisar la salida:

```bash
sudo -E SIPTIC_ASTERISK_ENV="$PWD/asterisk/.env" \
  ./asterisk/integrate.sh --apply
```

Este paso escribe archivos dedicados, hace copias en
`/var/backups/siptic-manager/asterisk/` y no recarga Asterisk. Para aplicar tras
una revisión final:

```bash
sudo -E SIPTIC_ASTERISK_ENV="$PWD/asterisk/.env" \
  ./asterisk/integrate.sh --apply --reload
```

La llamada a `Gosub(siptic-validar-horario,s,1(codename))` se coloca manualmente en la
ruta elegida. El instalador no modifica DIDs, endpoints, colas ni troncales.

## 6. Respaldos y restauración

```bash
./deploy/scripts/backup.sh
sudo ./deploy/systemd/install.sh
systemctl list-timers siptic-manager-backup.timer
```

Los respaldos quedan en `deploy/backups/`. Para restaurar:

```bash
./deploy/scripts/restore.sh deploy/backups/callcenter_manager_FECHA.dump
```

La restauración exige escribir `RESTAURAR` y genera un respaldo previo.

## 7. Actualizaciones

```bash
git pull --ff-only
./deploy/scripts/update.sh
```

El comando respalda primero, reconstruye la imagen, aplica migraciones mediante
el entrypoint y verifica el estado final.

## Diagnóstico

```bash
./deploy/scripts/status.sh
docker compose --env-file deploy/.env.production -f deploy/compose.yaml logs -f web
docker compose --env-file deploy/.env.production -f deploy/compose.yaml logs -f db
asterisk -rx "odbc show"
asterisk -rx "dialplan show siptic-validar-horario"
```
