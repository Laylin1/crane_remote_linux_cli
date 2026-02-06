#!/usr/bin/env bash
set -e

echo "=== Updating system ==="
sudo apt update && sudo apt upgrade -y

echo "=== Installing dependencies ==="
sudo apt install -y ca-certificates curl gnupg lsb-release python3 python3-pip git

echo "=== Installing Docker ==="
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


sudo groupadd docker || true
sudo usermod -aG docker $USER

echo "=== Installing Python dependencies ==="
pip3 install --upgrade pip

echo "=== Cloning project (если нужно) ==="
git clone <https://github.com/Laylin1/crane_remote_linux_cli.git> project || echo "Project already cloned"

echo "=== Building Docker images ==="
docker compose build

echo "=== Starting Docker containers ==="
docker compose up -d

echo "=== Все готово! ==="
