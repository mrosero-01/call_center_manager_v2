#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

require_env_file
"$DEPLOY_DIR/scripts/backup.sh"
compose build --pull web
compose up --detach db web
"$DEPLOY_DIR/scripts/status.sh"
