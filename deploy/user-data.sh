#!/bin/bash
# Script de arranque (User data) de la instancia EC2.
# Instala dependencias, clona el repositorio, configura variables de entorno
# y deja FastAPI corriendo como servicio systemd en el puerto 8000.
set -euxo pipefail

dnf install -y python3 python3-pip git

cd /home/ec2-user
sudo -u ec2-user git clone https://github.com/danielrodriguezaguirre12-del/acortador-enlaces.git
cd acortador-enlaces/backend
sudo -u ec2-user python3 -m venv .venv
sudo -u ec2-user .venv/bin/pip install -r requirements.txt

# IP publica de la instancia (IMDSv2) para construir los enlaces cortos
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)

cat > /etc/acortador.env <<EOF
AWS_REGION=us-east-1
TABLE_NAME=short_links
BASE_URL=http://$IP:8000
ALLOWED_ORIGINS=http://acortador-enlaces-daniel-uide.s3-website-us-east-1.amazonaws.com
EOF

cp /home/ec2-user/acortador-enlaces/deploy/acortador.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now acortador
