#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./setup-instance.sh <repo_url>
# Example:
#   ./setup-instance.sh https://github.com/your-org/VU-Chatbot.git

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <repo_url>"
  exit 1
fi

REPO_URL="$1"
APP_DIR="/opt/vu-chatbot"

sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER":"$USER" "$APP_DIR"

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --all
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/deploy/aws"

if [ ! -f .env.ec2 ]; then
  cp .env.ec2.example .env.ec2
  echo "Created .env.ec2 from template. Update secrets before starting."
  echo "Edit file: $APP_DIR/deploy/aws/.env.ec2"
  exit 0
fi

# Ensure runtime directories exist.
mkdir -p "$APP_DIR/data" "$APP_DIR/logs" "$APP_DIR/ssl"

# Build and run.
docker compose -f docker-compose.ec2.yml up -d --build

echo "Deployment complete. Check status with:"
echo "docker compose -f $APP_DIR/deploy/aws/docker-compose.ec2.yml ps"
