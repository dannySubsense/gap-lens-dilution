#!/usr/bin/env bash
# Install + start gaplens-frontend.service (supervised Next.js prod server on :3001).
# Mirrors gaplens-backend.service (Restart=always, User=d-tuned, multi-user.target).
#
# Needs sudo (writes to /etc/systemd/system). Run it directly:
#   bash deploy/install-frontend-service.sh
# or from inside a Claude Code session:
#   ! bash deploy/install-frontend-service.sh
#
# Safe to re-run. It hands the port over from any manually-started `next start`
# process so there is no port-in-use conflict.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
UNIT_SRC="$HERE/gaplens-frontend.service"
UNIT_DST="/etc/systemd/system/gaplens-frontend.service"

echo "[1/5] Installing unit -> $UNIT_DST"
sudo cp "$UNIT_SRC" "$UNIT_DST"

echo "[2/5] daemon-reload + enable (start on boot)"
sudo systemctl daemon-reload
sudo systemctl enable gaplens-frontend

echo "[3/5] Releasing :3001 from any manually-started next process"
pkill -f "next start -p 3001" 2>/dev/null || true
sleep 1

echo "[4/5] Starting service"
sudo systemctl start gaplens-frontend
sleep 2

echo "[5/5] Verify"
systemctl is-active gaplens-frontend
curl -s -o /dev/null -w "frontend :3001 -> %{http_code}\n" http://localhost:3001/
echo "Done. Tail logs with: journalctl -u gaplens-frontend -f"
