#!/bin/bash
# Manual setup script for EC2 instance
# Run this if user data script didn't complete

set -e

echo "=== Setting up DRP SpokesBot on EC2 ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit 1
fi

# Update system
echo "Updating system..."
yum update -y

# Install Python 3 and dependencies
echo "Installing Python and dependencies..."
# Note: curl is already installed as curl-minimal on Amazon Linux 2023
yum install -y python3 python3-pip python3-devel gcc git

# Install Ollama
echo "Installing Ollama..."
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama already installed"
fi

# Install Nginx
echo "Installing Nginx..."
yum install -y nginx

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

# Create systemd service for Ollama
echo "Creating Ollama systemd service..."
cat > /etc/systemd/system/ollama.service << 'OLLAMA_EOF'
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
OLLAMA_EOF

# Create systemd service for FastAPI app
echo "Creating FastAPI systemd service..."
cat > /etc/systemd/system/drp-spokesbot.service << 'APP_EOF'
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
APP_EOF

# Configure Nginx reverse proxy
echo "Configuring Nginx..."
cat > /etc/nginx/conf.d/partybot.conf << 'NGINX_EOF'
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
NGINX_EOF

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
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
  if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  if [ $((i % 5)) -eq 0 ]; then
    echo "Waiting for Ollama... ($i/30)"
  fi
  sleep 2
done

# Pull required models (non-blocking)
echo "Pulling models (this may take a while)..."
su - ollama -c "ollama pull qwen3:0.6b" || echo "Note: Model pull may continue in background"
su - ollama -c "ollama pull qwen3-embedding:0.6b" || echo "Note: Model pull may continue in background"

# Start Nginx
echo "Starting Nginx..."
systemctl start nginx

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. cd /opt/partybot"
echo "2. git clone https://github.com/yourusername/partybot.git ."
echo "3. /opt/partybot/venv/bin/pip install -r requirements.txt"
echo "4. systemctl start drp-spokesbot"
echo ""
echo "Check status:"
echo "  systemctl status ollama"
echo "  systemctl status drp-spokesbot"
echo "  systemctl status nginx"

