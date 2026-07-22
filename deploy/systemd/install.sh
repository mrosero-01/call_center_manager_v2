#!/bin/sh
set -eu

[ "$(id -u)" -eq 0 ] || {
    echo "Este instalador requiere root." >&2
    exit 1
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
service=/etc/systemd/system/siptic-manager-backup.service
timer=/etc/systemd/system/siptic-manager-backup.timer

sed "s@__PROJECT_DIR__@$PROJECT_DIR@g" \
    "$SCRIPT_DIR/siptic-manager-backup.service.template" > "$service"
install -m 0644 "$SCRIPT_DIR/siptic-manager-backup.timer" "$timer"
systemctl daemon-reload
systemctl enable --now siptic-manager-backup.timer
systemctl list-timers siptic-manager-backup.timer
