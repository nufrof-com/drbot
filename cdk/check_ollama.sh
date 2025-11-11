#!/bin/bash
# Quick script to check Ollama status and fix issues

echo "=== Checking Ollama Status ==="

# Check if Ollama service is running
echo "1. Service Status:"
sudo systemctl status ollama --no-pager -l | head -15

echo ""
echo "2. Ollama Process:"
ps aux | grep ollama | grep -v grep || echo "No Ollama process found"

echo ""
echo "3. Port 11434:"
sudo netstat -tlnp | grep 11434 || echo "Port 11434 not listening"

echo ""
echo "4. Test Connection:"
curl -f http://localhost:11434/api/tags 2>&1 | head -5 || echo "Cannot connect to Ollama"

echo ""
echo "5. Models Available:"
sudo -u ollama ollama list 2>&1 || echo "Cannot list models"

echo ""
echo "=== Fixes ==="

# Check if service is running
if ! systemctl is-active --quiet ollama; then
  echo "❌ Ollama service is not running"
  echo "Starting Ollama..."
  sudo systemctl start ollama
  sleep 5
fi

# Check if port is listening
if ! sudo netstat -tlnp | grep -q 11434; then
  echo "❌ Ollama is not listening on port 11434"
  echo "Restarting Ollama..."
  sudo systemctl restart ollama
  sleep 10
fi

# Check if models are available
if ! sudo -u ollama ollama list 2>&1 | grep -q "qwen3:0.6b"; then
  echo "❌ Models not found"
  echo "Pulling models..."
  sudo -u ollama ollama pull qwen3:0.6b
  sudo -u ollama ollama pull qwen3-embedding:0.6b
fi

echo ""
echo "=== Final Check ==="
curl -f http://localhost:11434/api/tags && echo "✅ Ollama is working!" || echo "❌ Ollama still not working"

