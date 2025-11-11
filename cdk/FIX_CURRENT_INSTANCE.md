# Fix Current EC2 Instance

The user data script failed due to a package conflict. Here's how to fix the current instance:

## Quick Fix Commands

Run these on your EC2 instance:

```bash
# 1. Create the directory
sudo mkdir -p /opt/partybot
sudo chown ec2-user:ec2-user /opt/partybot

# 2. Install Python and dependencies (curl is already installed)
sudo yum install -y python3 python3-pip python3-devel gcc git

# 3. Install Ollama (if not already installed)
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# 4. Install Nginx
sudo yum install -y nginx

# 5. Create Python virtual environment
cd /opt/partybot
sudo python3 -m venv /opt/partybot/venv
sudo chown -R ec2-user:ec2-user /opt/partybot/venv

# 6. Create Ollama systemd service
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
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

# 7. Create FastAPI systemd service
sudo tee /etc/systemd/system/drp-spokesbot.service > /dev/null << 'EOF'
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

# 8. Configure Nginx
sudo tee /etc/nginx/conf.d/partybot.conf > /dev/null << 'EOF'
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

# 9. Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl enable nginx
sudo systemctl enable drp-spokesbot

# 10. Start Ollama
sudo systemctl start ollama

# 11. Wait for Ollama and pull models
echo "Waiting for Ollama..."
sleep 10
for i in {1..30}; do
  if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  sleep 2
done

# Pull models (this takes a while)
echo "Pulling models..."
sudo -u ollama ollama pull qwen3:0.6b || echo "Model pull may continue in background"
sudo -u ollama ollama pull qwen3-embedding:0.6b || echo "Model pull may continue in background"

# 12. Start Nginx
sudo systemctl start nginx

# 13. Verify services
sudo systemctl status ollama
sudo systemctl status nginx
```

## Next Steps

After running the above:

```bash
# Clone your repository
cd /opt/partybot
git clone https://github.com/yourusername/partybot.git .

# Install Python dependencies
/opt/partybot/venv/bin/pip install -r requirements.txt

# Start the application
sudo systemctl start drp-spokesbot

# Check logs
sudo journalctl -u drp-spokesbot -f
```

## For Future Deployments

The CDK stack has been fixed. When you deploy a new instance, it will work correctly.

