#!/bin/bash
# Script to manually complete the user data setup on an existing instance
# Run this on the EC2 instance if user data didn't complete

set -e

echo "=== Completing User Data Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit 1
fi

LOG_FILE=/var/log/user-data-manual.log
touch $LOG_FILE
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "[$(date)] Starting manual user data completion"

# Install Ollama
echo "Installing Ollama..."
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh || { echo "Ollama installation failed"; exit 1; }
else
  echo "Ollama already installed"
fi

# Install Nginx
echo "Installing Nginx..."
yum install -y nginx || { echo "Nginx installation failed"; exit 1; }

# Create app directory
echo "Creating app directory..."
mkdir -p /opt/partybot
chown ec2-user:ec2-user /opt/partybot

# Create Python virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "/opt/partybot/venv" ]; then
  python3 -m venv /opt/partybot/venv
  chown -R ec2-user:ec2-user /opt/partybot/venv
else
  echo "Virtual environment already exists"
fi

# Create Ollama systemd service
echo "Creating Ollama systemd service..."
cat > /etc/systemd/system/ollama.service << 'EOF'
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create FastAPI systemd service
echo "Creating FastAPI systemd service..."
cat > /etc/systemd/system/drp-spokesbot.service << 'EOF'
[Unit]
Description=DRP SpokesBot FastAPI Application
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/partybot
Environment="PATH=/opt/partybot/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="OLLAMA_BASE_URL=http://localhost:11434"
ExecStart=/opt/partybot/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/conf.d/partybot.conf << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

# Enable and start services
echo "Enabling services..."
systemctl daemon-reload
systemctl enable ollama
systemctl enable nginx
systemctl enable drp-spokesbot

# Start Ollama
echo "Starting Ollama..."
systemctl start ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama..."
sleep 10
for i in {1..30}; do
  if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  sleep 2
done

# Pull required models
echo "Pulling models..."
su - ollama -c "ollama pull qwen3:0.6b" || echo "Model pull may continue in background"
su - ollama -c "ollama pull qwen3-embedding:0.6b" || echo "Model pull may continue in background"

# Start Nginx
echo "Starting Nginx..."
systemctl start nginx

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. cd /opt/partybot"
echo "2. git clone https://github.com/nufrof-com/drbot.git ."
echo "3. /opt/partybot/venv/bin/pip install -r requirements.txt"
echo "4. systemctl start drp-spokesbot"
echo ""
echo "Check status:"
echo "  systemctl status ollama"
echo "  systemctl status drp-spokesbot"
echo "  systemctl status nginx"

