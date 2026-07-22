#!/bin/sh
set -eu
. "$(dirname -- "$0")/common.sh"

require_env_file
mkdir -p "$DEPLOY_DIR/backups"
chmod 700 "$DEPLOY_DIR/backups"
compose --profile manual run --rm backup
