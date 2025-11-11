# EC2 Deployment Guide

This guide covers deploying the Democratic Republican SpokesBot to an AWS EC2 instance.

## Prerequisites

1. **AWS Account** with EC2 access
2. **EC2 Instance** (recommended: t3.medium or larger, Ubuntu 22.04 LTS)
3. **SSH access** to your EC2 instance
4. **Domain name** (optional, for custom domain)

## Step 1: Launch EC2 Instance

### Instance Requirements

- **Instance Type**: t3.medium or larger (minimum 2 vCPU, 4GB RAM)
  - t3.medium: 2 vCPU, 4GB RAM (minimum)
  - t3.large: 2 vCPU, 8GB RAM (recommended for better performance)
- **OS**: Ubuntu 22.04 LTS (recommended)
- **Storage**: 20GB minimum (for models and data)
- **Security Group**: Open ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Launch Steps

1. Go to AWS Console → EC2 → Launch Instance
2. Choose Ubuntu 22.04 LTS
3. Select instance type (t3.medium or larger)
4. Configure security group:
   - SSH (22) from your IP
   - HTTP (80) from anywhere (0.0.0.0/0)
   - HTTPS (443) from anywhere (0.0.0.0/0)
5. Create/select a key pair for SSH access
6. Launch instance

## Step 2: Connect to EC2 Instance

```bash
# Replace with your key file and instance IP
ssh -i your-key.pem ubuntu@your-ec2-ip
```

## Step 3: Install Dependencies

### Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
exit
# Then SSH back in
```

### Install Git

```bash
sudo apt install git -y
```

## Step 4: Clone and Setup Application

```bash
# Clone your repository
git clone https://github.com/yourusername/partybot.git
cd partybot

# Or if you're uploading files directly, create the directory
# mkdir -p /home/ubuntu/partybot
# cd /home/ubuntu/partybot
# Upload your files here
```

## Step 5: Create Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: drp-ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"  # Only accessible locally
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: drp-spokesbot-app
    depends_on:
      ollama:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible locally (nginx will proxy)
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_LLM_MODEL=qwen3:0.6b
      - OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b
      - PARTY_NAME=Democratic Republicans
      - BOT_NAME=Democratic Republican SpokesBot
      - RATE_LIMIT_PER_MINUTE=10
      - CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
      - DATA_DIRECTORY=drp_platform/platform
    volumes:
      - ./data:/app/data
      - ./drp_platform:/app/drp_platform
      - ./static:/app/static
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: drp-nginx
    depends_on:
      - app
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # For SSL certificates (if using HTTPS)
    restart: unless-stopped

volumes:
  ollama_data:
```

## Step 6: Create Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;

    server {
        listen 80;
        server_name your-domain.com;  # Replace with your domain or EC2 IP

        # Redirect HTTP to HTTPS (if using SSL)
        # return 301 https://$server_name$request_uri;

        # Or serve directly on HTTP
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Rate limiting
            limit_req zone=api_limit burst=5 nodelay;
        }

        # Health check endpoint (no rate limit)
        location /health {
            proxy_pass http://app;
            access_log off;
        }
    }

    # HTTPS server (uncomment if using SSL)
    # server {
    #     listen 443 ssl http2;
    #     server_name your-domain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     location / {
    #         proxy_pass http://app;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #
    #         limit_req zone=api_limit burst=5 nodelay;
    #     }
    #
    #     location /health {
    #         proxy_pass http://app;
    #         access_log off;
    #     }
    # }
}
```

## Step 7: Update Dockerfile for Production

Your existing `Dockerfile` should work, but make sure it doesn't include Ollama (since we're running it separately):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY static/ ./static/
COPY drp_platform/ ./drp_platform/

# Create chroma_db directory
RUN mkdir -p /app/data/chroma_db

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Step 8: Deploy

```bash
# Build and start services
docker compose -f docker-compose.prod.yml up --build -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check status
docker compose -f docker-compose.prod.yml ps
```

## Step 9: Setup Auto-restart on Reboot

Create a systemd service to auto-start on reboot:

```bash
sudo nano /etc/systemd/system/drp-spokesbot.service
```

Add:

```ini
[Unit]
Description=DRP SpokesBot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/partybot
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable drp-spokesbot.service
sudo systemctl start drp-spokesbot.service
```

## Step 10: Setup SSL (Optional but Recommended)

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to project directory
sudo mkdir -p /home/ubuntu/partybot/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /home/ubuntu/partybot/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /home/ubuntu/partybot/ssl/key.pem
sudo chown -R ubuntu:ubuntu /home/ubuntu/partybot/ssl

# Update nginx.conf to use HTTPS (uncomment HTTPS server block)
# Then restart nginx container
docker compose -f docker-compose.prod.yml restart nginx
```

## Step 11: Update Application

```bash
cd /home/ubuntu/partybot

# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up --build -d
```

## Monitoring

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f ollama
```

### Check Health

```bash
# From your local machine
curl http://your-ec2-ip/health

# Or from EC2
curl http://localhost:8000/health
```

### Monitor Resources

```bash
# Check Docker containers
docker ps

# Check system resources
htop
# or
free -h
df -h
```

## Security Considerations

1. **Firewall**: Use AWS Security Groups to restrict access
2. **SSH**: Use key-based authentication, disable password login
3. **Rate Limiting**: Already configured in nginx and app
4. **HTTPS**: Use SSL certificates (Let's Encrypt is free)
5. **Updates**: Keep system and Docker images updated
6. **Backups**: Regularly backup ChromaDB data

## Cost Optimization

- **Instance Type**: Start with t3.medium, scale up if needed
- **Reserved Instances**: Save up to 72% with 1-3 year commitments
- **Auto-shutdown**: Consider stopping instance during off-hours
- **Storage**: Use EBS volumes, delete unused snapshots

## Troubleshooting

### App not accessible

```bash
# Check if containers are running
docker ps

# Check nginx logs
docker compose -f docker-compose.prod.yml logs nginx

# Check app logs
docker compose -f docker-compose.prod.yml logs app

# Test app directly
curl http://localhost:8000/health
```

### Out of memory

```bash
# Check memory usage
free -h

# If low, upgrade instance type or add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Models not loading

```bash
# Check Ollama logs
docker compose -f docker-compose.prod.yml logs ollama

# Pull models manually
docker exec -it drp-ollama ollama pull qwen3:0.6b
docker exec -it drp-ollama ollama pull qwen3-embedding:0.6b
```

## Quick Reference

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d

# Stop services
docker compose -f docker-compose.prod.yml down

# Restart services
docker compose -f docker-compose.prod.yml restart

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Rebuild after code changes
docker compose -f docker-compose.prod.yml up --build -d

# Check status
docker compose -f docker-compose.prod.yml ps
```

