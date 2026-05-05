#!/bin/bash
# EventManagement — GCloud VM setup script
# VM: skycam-worker-01 (34.154.177.76)
# Run as: nhorncastle (with sudo)

APP_DIR="/opt/eventmanagement"
VENV="$APP_DIR/venv"
DOMAIN="events.ego2.net"
PORT=5003

echo "=== EventManagement VM Setup ==="

# 1. Create app directory
sudo mkdir -p $APP_DIR/static/uploads
sudo chown -R nhorncastle:nhorncastle $APP_DIR

# 2. Python virtual environment
python3 -m venv $VENV
$VENV/bin/pip install --upgrade pip
$VENV/bin/pip install flask flask-sqlalchemy flask-login gunicorn werkzeug qrcode pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib

# 3. Environment file
cat > $APP_DIR/env.py << 'ENVEOF'
import os
os.environ.setdefault('SMTP_EMAIL', 'marinaclubes@gmail.com')
os.environ.setdefault('SMTP_PASSWORD', 'efzc brhm kfsv hbke')
ENVEOF

# 4. Gunicorn systemd service
sudo tee /etc/systemd/system/eventmanagement.service > /dev/null << SVCEOF
[Unit]
Description=EventManagement Flask App
After=network.target

[Service]
User=nhorncastle
WorkingDirectory=$APP_DIR
ExecStart=$VENV/bin/gunicorn -w 2 -b 127.0.0.1:$PORT "app:app" --timeout 120 --access-logfile $APP_DIR/access.log --error-logfile $APP_DIR/error.log
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=APP_URL=https://events.ego2.net
Environment=SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable eventmanagement

# 5. Nginx site config
sudo tee /etc/nginx/sites-available/eventmanagement > /dev/null << NGXEOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
NGXEOF

sudo ln -sf /etc/nginx/sites-available/eventmanagement /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "1. Copy app files to $APP_DIR"
echo "2. sudo systemctl start eventmanagement"
echo "3. sudo certbot --nginx -d $DOMAIN"
echo "4. Point DNS A-record for $DOMAIN to 34.154.177.76"
