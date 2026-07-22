#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE=${SIPTIC_ASTERISK_ENV:-$SCRIPT_DIR/.env}
MODE=${1:---check}
RELOAD=${2:-}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

case "$MODE" in
  --check|--dry-run|--apply|--rollback) ;;
  *) die "Uso: $0 --check|--dry-run|--apply [--reload]|--rollback" ;;
esac

[[ -f "$ENV_FILE" ]] || die "Falta $ENV_FILE. Copia asterisk/.env.example."
# shellcheck disable=SC1090
source "$ENV_FILE"

required=(
  ASTERISK_DB_HOST ASTERISK_DB_PORT ASTERISK_DB_NAME ASTERISK_DB_USER
  ASTERISK_DB_PASSWORD ASTERISK_ODBC_DSN ASTERISK_ODBC_DRIVER
  ASTERISK_CONFIG_DIR ASTERISK_SOUND_DIR
)
for key in "${required[@]}"; do
  [[ -n "${!key:-}" ]] || die "Falta $key en $ENV_FILE"
done

[[ "$ASTERISK_ODBC_DSN" =~ ^[a-zA-Z0-9_-]+$ ]] || die "DSN ODBC inválido."
[[ "$ASTERISK_DB_USER" =~ ^[a-z_][a-z0-9_]*$ ]] || die "Usuario PostgreSQL inválido."
[[ "$ASTERISK_DB_PORT" =~ ^[0-9]+$ ]] || die "Puerto PostgreSQL inválido."

odbc_file=/etc/odbc.ini
res_file=$ASTERISK_CONFIG_DIR/siptic_manager_res_odbc.conf
func_file=$ASTERISK_CONFIG_DIR/siptic_manager_func_odbc.conf
dialplan_file=$ASTERISK_CONFIG_DIR/siptic_manager_dialplan.conf
marker_start="# BEGIN SIPTIC MANAGER ODBC"
marker_end="# END SIPTIC MANAGER ODBC"

render() {
  local source=$1 target=$2
  sed \
    -e "s@__ODBC_DSN__@$ASTERISK_ODBC_DSN@g" \
    -e "s@__ODBC_DRIVER__@$ASTERISK_ODBC_DRIVER@g" \
    -e "s@__DB_HOST__@$ASTERISK_DB_HOST@g" \
    -e "s@__DB_PORT__@$ASTERISK_DB_PORT@g" \
    -e "s@__DB_NAME__@$ASTERISK_DB_NAME@g" \
    -e "s@__DB_USER__@$ASTERISK_DB_USER@g" \
    -e "s@__DB_PASSWORD__@$ASTERISK_DB_PASSWORD@g" \
    "$source" > "$target"
}

remove_managed_odbc_block() {
  local temporary
  temporary=$(mktemp)
  awk -v start="$marker_start" -v end="$marker_end" '
    $0 == start {skip=1; next}
    $0 == end {skip=0; next}
    !skip {print}
  ' "$odbc_file" > "$temporary"
  cat "$temporary" > "$odbc_file"
  rm -f "$temporary"
}

remove_include() {
  local base_file=$1 included_name=$2 temporary
  [[ -f "$base_file" ]] || return 0
  temporary=$(mktemp)
  grep -Fvx "#include $included_name" "$base_file" > "$temporary" || true
  cat "$temporary" > "$base_file"
  rm -f "$temporary"
}

if [[ "$MODE" == "--rollback" ]]; then
  [[ $(id -u) -eq 0 ]] || die "--rollback requiere root."
  [[ -f "$odbc_file" ]] && grep -Fq "$marker_start" "$odbc_file" && remove_managed_odbc_block
  remove_include "$ASTERISK_CONFIG_DIR/res_odbc.conf" "$(basename "$res_file")"
  remove_include "$ASTERISK_CONFIG_DIR/func_odbc.conf" "$(basename "$func_file")"
  remove_include "$ASTERISK_CONFIG_DIR/extensions.conf" "$(basename "$dialplan_file")"
  rm -f "$res_file" "$func_file" "$dialplan_file"
  rm -f "$ASTERISK_SOUND_DIR/falla_tecnica.wav" "$ASTERISK_SOUND_DIR/reentrenamiento_personal.wav"
  echo "Se retiraron únicamente los archivos y líneas administrados por Siptic Manager."
  exit 0
fi

for command in asterisk isql odbcinst timeout; do
  command -v "$command" >/dev/null 2>&1 || die "Falta el comando $command"
done
id asterisk >/dev/null 2>&1 || die "No existe el usuario de sistema asterisk."
odbcinst -q -d | grep -Fqx "[$ASTERISK_ODBC_DRIVER]" || \
  die "No está instalado el driver ODBC: $ASTERISK_ODBC_DRIVER"
[[ -d "$ASTERISK_CONFIG_DIR" ]] || die "No existe $ASTERISK_CONFIG_DIR"
[[ -f "$ASTERISK_CONFIG_DIR/extensions.conf" ]] || die "No existe extensions.conf"

if ! timeout 3 bash -c "</dev/tcp/$ASTERISK_DB_HOST/$ASTERISK_DB_PORT" 2>/dev/null; then
  die "No hay conexión TCP con PostgreSQL en $ASTERISK_DB_HOST:$ASTERISK_DB_PORT."
fi

if [[ -f "$odbc_file" ]] && grep -Eq "^\[$ASTERISK_ODBC_DSN\]$" "$odbc_file" \
  && ! grep -Fq "$marker_start" "$odbc_file"; then
  die "Ya existe el DSN $ASTERISK_ODBC_DSN y no pertenece a Siptic Manager."
fi

if [[ "$MODE" == "--check" ]]; then
  echo "Asterisk encontrado: $(asterisk -rx 'core show version' | head -n 1)"
  echo "No se detectaron conflictos con el DSN ni los archivos dedicados."
  echo "PostgreSQL esperado en $ASTERISK_DB_HOST:$ASTERISK_DB_PORT."
  exit 0
fi

if [[ "$MODE" == "--dry-run" ]]; then
  echo "Se creará un DSN dedicado en $odbc_file (contraseña oculta)."
  echo "Se crearán:"
  echo "  $res_file"
  echo "  $func_file"
  echo "  $dialplan_file"
  echo "  $ASTERISK_SOUND_DIR/{falla_tecnica,reentrenamiento_personal}.wav"
  echo "Se agregarán tres líneas #include; no se editarán rutas, colas, troncales ni endpoints."
  exit 0
fi

[[ $(id -u) -eq 0 ]] || die "--apply requiere root."

backup_dir=/var/backups/siptic-manager/asterisk/$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$backup_dir"
for file in "$odbc_file" "$ASTERISK_CONFIG_DIR/res_odbc.conf" \
  "$ASTERISK_CONFIG_DIR/func_odbc.conf" "$ASTERISK_CONFIG_DIR/extensions.conf"; do
  [[ ! -f "$file" ]] || cp -a "$file" "$backup_dir/"
done

temporary_odbc=$(mktemp)
temporary_res=$(mktemp)
trap 'rm -f "$temporary_odbc" "$temporary_res"' EXIT
render "$SCRIPT_DIR/odbc_siptic.ini.template" "$temporary_odbc"
render "$SCRIPT_DIR/res_odbc_siptic.conf.template" "$temporary_res"

touch "$odbc_file"
if grep -Fq "$marker_start" "$odbc_file"; then
  remove_managed_odbc_block
fi
{
  echo "$marker_start"
  cat "$temporary_odbc"
  echo "$marker_end"
} >> "$odbc_file"
chmod 0644 "$odbc_file"

config_group=root
getent group asterisk >/dev/null && config_group=asterisk
install -o root -g "$config_group" -m 0640 "$temporary_res" "$res_file"
install -o root -g "$config_group" -m 0640 "$SCRIPT_DIR/func_odbc_callcenter.conf.example" "$func_file"
install -o root -g "$config_group" -m 0640 "$SCRIPT_DIR/validar_horario.conf.example" "$dialplan_file"

for pair in \
  "$ASTERISK_CONFIG_DIR/res_odbc.conf:$(basename "$res_file")" \
  "$ASTERISK_CONFIG_DIR/func_odbc.conf:$(basename "$func_file")" \
  "$ASTERISK_CONFIG_DIR/extensions.conf:$(basename "$dialplan_file")"; do
  base=${pair%%:*}
  include=${pair#*:}
  touch "$base"
  grep -Fqx "#include $include" "$base" || echo "#include $include" >> "$base"
done

install -d -o asterisk -g asterisk -m 0755 "$ASTERISK_SOUND_DIR"
install -o asterisk -g asterisk -m 0644 \
  "$SCRIPT_DIR/sounds/callcenter_manager/falla_tecnica.wav" \
  "$SCRIPT_DIR/sounds/callcenter_manager/reentrenamiento_personal.wav" \
  "$ASTERISK_SOUND_DIR/"

if ! isql -b "$ASTERISK_ODBC_DSN" "$ASTERISK_DB_USER" "$ASTERISK_DB_PASSWORD" >/dev/null; then
  die "ODBC no pudo conectar. No se recargó Asterisk. Respaldos: $backup_dir"
fi

echo "Integración escrita y conexión ODBC correcta. Respaldos: $backup_dir"

if [[ "$RELOAD" == "--reload" ]]; then
  asterisk -rx "module reload res_odbc.so"
  asterisk -rx "module reload func_odbc.so"
  asterisk -rx "dialplan reload"
  asterisk -rx "odbc show"
  echo "Asterisk recargado. Falta conectar Gosub(siptic-validar-horario,s,1(codename)) en la ruta elegida."
else
  echo "No se recargó Asterisk. Revisa los archivos y repite con --apply --reload."
fi
