#!/usr/bin/env bash
# PostgreSQL backup for compose.vps.yml, run by the server administrator.
set -euo pipefail
umask 077
crm_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backup_dir="${1:-/var/backups/invekta-crm}"
mkdir -p -- "$backup_dir"
chmod 700 -- "$backup_dir"
cd -- "$crm_root"
backup_file="$backup_dir/crm-$(date -u +%Y%m%dT%H%M%SZ)-$$.dump"
backup_tmp="$backup_file.partial"
trap 'rm -f -- "$backup_tmp"' EXIT
docker compose --env-file .env.production -f compose.vps.yml exec -T db pg_dump -U crm -d crm -Fc > "$backup_tmp"
test -s "$backup_tmp"
# Validate the archive directory; a separate restore test is still required.
docker compose --env-file .env.production -f compose.vps.yml exec -T db pg_restore --list < "$backup_tmp" > /dev/null
mv -- "$backup_tmp" "$backup_file"
printf 'Backup saved: %s\n' "$backup_file"
