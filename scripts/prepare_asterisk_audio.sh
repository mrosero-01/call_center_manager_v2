#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_AUDIO_DIR="$ROOT_DIR/static/audio/schedules"
ASTERISK_AUDIO_DIR="$ROOT_DIR/asterisk/sounds/callcenter_manager"

FILES=(
  "falla_tecnica"
  "reentrenamiento_personal"
)

if ! command -v sox >/dev/null 2>&1; then
  echo "SoX no está instalado. Instálalo antes de convertir audios." >&2
  exit 1
fi

mkdir -p "$ASTERISK_AUDIO_DIR"

for name in "${FILES[@]}"; do
  source_file="$WEB_AUDIO_DIR/$name.mp3"
  target_file="$ASTERISK_AUDIO_DIR/$name.wav"

  if [ ! -f "$source_file" ]; then
    echo "Falta $source_file" >&2
    exit 1
  fi

  sox \
    -G \
    "$source_file" \
    -r 8000 \
    -c 1 \
    -e signed-integer \
    -b 16 \
    "$target_file"

  soxi "$target_file"
done

if [ "${ASTERISK_SOUNDS_DIR:-}" != "" ]; then
  mkdir -p "$ASTERISK_SOUNDS_DIR"
  for name in "${FILES[@]}"; do
    install \
      -m 0644 \
      "$ASTERISK_AUDIO_DIR/$name.wav" \
      "$ASTERISK_SOUNDS_DIR/$name.wav"
  done

  if [ "$(id -u)" -eq 0 ] && id asterisk >/dev/null 2>&1; then
    chown asterisk:asterisk "$ASTERISK_SOUNDS_DIR"/*.wav
  fi

  echo "Audios copiados a $ASTERISK_SOUNDS_DIR"
else
  echo "Audios preparados en $ASTERISK_AUDIO_DIR"
  echo "Para instalar en Asterisk:"
  echo "ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom/callcenter_manager $0"
fi
