#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_AUDIO_DIR="$ROOT_DIR/static/audio/schedules"
ASTERISK_AUDIO_DIR="$ROOT_DIR/asterisk/sounds/callcenter_manager"

FILES=(
  "schedule_changed"
  "temporarily_unavailable"
  "special_day"
)

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg no está instalado. Instálalo antes de convertir audios." >&2
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

  ffmpeg \
    -y \
    -i "$source_file" \
    -ar 8000 \
    -ac 1 \
    -sample_fmt s16 \
    "$target_file"
done

if [ "${ASTERISK_SOUNDS_DIR:-}" != "" ]; then
  mkdir -p "$ASTERISK_SOUNDS_DIR"
  cp "$ASTERISK_AUDIO_DIR"/*.wav "$ASTERISK_SOUNDS_DIR"/
  echo "Audios copiados a $ASTERISK_SOUNDS_DIR"
else
  echo "Audios preparados en $ASTERISK_AUDIO_DIR"
  echo "Para instalar en Asterisk:"
  echo "ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/custom/callcenter_manager $0"
fi
