#!/usr/bin/env bash
# Runs once on first boot via EC2 user_data.
# Installs Docker, docker-compose, AWS CLI, and the Cloudflare tunnel daemon.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
AWS_REGION="ap-southeast-1"

log() { echo "[bootstrap] $*"; }

# ── System updates ────────────────────────────────────────────────────────────
log "Updating system packages"
apt-get update -y
apt-get upgrade -y

# ── Docker ────────────────────────────────────────────────────────────────────
log "Installing Docker"
apt-get install -y --no-install-recommends ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y --no-install-recommends \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group so SSH deploys don't need sudo
usermod -aG docker ubuntu

# ── AWS CLI v2 ────────────────────────────────────────────────────────────────
log "Installing AWS CLI v2"
apt-get install -y --no-install-recommends unzip
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install
rm -rf /tmp/awscliv2.zip /tmp/aws

# ── App directory ─────────────────────────────────────────────────────────────
log "Creating app directory"
mkdir -p /opt/app
chown ubuntu:ubuntu /opt/app

# ── ECR login helper (runs on every Docker start) ─────────────────────────────
log "Installing ECR credential helper"
apt-get install -y --no-install-recommends amazon-ecr-credential-helper

mkdir -p /home/ubuntu/.docker
cat > /home/ubuntu/.docker/config.json <<EOF
{
  "credHelpers": {
    "$(aws ecr describe-registry --region $AWS_REGION --query 'registryId' --output text 2>/dev/null || echo 'public.ecr.aws').dkr.ecr.$AWS_REGION.amazonaws.com": "ecr-login"
  }
}
EOF
chown -R ubuntu:ubuntu /home/ubuntu/.docker

# ── CloudWatch agent ──────────────────────────────────────────────────────────
log "Installing CloudWatch agent"
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb \
  -O /tmp/amazon-cloudwatch-agent.deb
dpkg -i /tmp/amazon-cloudwatch-agent.deb
rm /tmp/amazon-cloudwatch-agent.deb

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/tiktok-ai/system",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

log "Bootstrap complete. SSH in as ubuntu and run the deploy workflow."
