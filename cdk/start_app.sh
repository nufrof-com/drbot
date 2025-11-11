#!/bin/bash
# Quick script to start the application and check status

echo "=== Starting DRP SpokesBot ==="

# Check if code is deployed
if [ ! -d "/opt/partybot/app" ]; then
  echo "ERROR: Application code not found in /opt/partybot"
  echo "Please run:"
  echo "  cd /opt/partybot"
  echo "  git clone https://github.com/nufrof-com/drbot.git ."
  echo "  /opt/partybot/venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Check if dependencies are installed
if [ ! -f "/opt/partybot/venv/bin/uvicorn" ]; then
  echo "Installing Python dependencies..."
  /opt/partybot/venv/bin/pip install -r requirements.txt || {
    echo "ERROR: Failed to install dependencies"
    exit 1
  }
fi

# Check Ollama status
echo "Checking Ollama..."
if ! systemctl is-active --quiet ollama; then
  echo "Starting Ollama..."
  sudo systemctl start ollama
  sleep 5
fi

# Check if models are available
echo "Checking for models..."
if ! sudo -u ollama ollama list 2>/dev/null | grep -q "qwen3:0.6b"; then
  echo "Models not found. Pulling models (this may take a while)..."
  sudo -u ollama ollama pull qwen3:0.6b || echo "Warning: Model pull failed"
  sudo -u ollama ollama pull qwen3-embedding:0.6b || echo "Warning: Model pull failed"
fi

# Start the application
echo "Starting application..."
sudo systemctl start drp-spokesbot

# Wait a moment
sleep 3

# Check status
echo ""
echo "=== Service Status ==="
sudo systemctl status drp-spokesbot --no-pager

echo ""
echo "=== Recent Logs ==="
sudo journalctl -u drp-spokesbot -n 20 --no-pager

echo ""
if systemctl is-active --quiet drp-spokesbot; then
  echo "✅ Application is running!"
  echo "Check logs with: sudo journalctl -u drp-spokesbot -f"
else
  echo "❌ Application failed to start. Check logs above for errors."
  echo "View full logs: sudo journalctl -u drp-spokesbot -n 50"
fi

