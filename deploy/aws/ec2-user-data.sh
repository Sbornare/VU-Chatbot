#!/usr/bin/env bash
set -euo pipefail

# User-data script for Amazon Linux 2023 EC2 instances.
# Installs Docker, Docker Compose plugin, git, and enables Docker on boot.
sudo dnf update -y
sudo dnf install -y docker git

sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose plugin if not already available.
if ! docker compose version >/dev/null 2>&1; then
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -SL "https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

# Allow ec2-user to run docker without sudo.
sudo usermod -aG docker ec2-user

echo "Bootstrap complete. Re-login once to apply docker group membership."
