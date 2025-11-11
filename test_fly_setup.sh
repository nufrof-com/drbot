#!/bin/bash
# Test script to verify Fly.io setup works locally

set -e

echo "🧪 Testing Fly.io Setup Locally"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check if container is running
if docker ps | grep -q "drp-spokesbot-fly-test"; then
    echo -e "${GREEN}✅ Container is running${NC}"
else
    echo -e "${YELLOW}⚠️  Container is not running. Starting it...${NC}"
    echo "Run: docker compose -f docker-compose.fly.yml up --build -d"
    echo "     (or: docker-compose -f docker-compose.fly.yml up --build -d)"
    echo ""
    read -p "Press Enter to continue after starting the container, or Ctrl+C to exit..."
fi

echo ""
echo "Waiting for app to be ready..."
echo ""

# Wait for health endpoint
MAX_ATTEMPTS=60
ATTEMPT=0
HEALTHY=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ App is healthy!${NC}"
        HEALTHY=1
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $((ATTEMPT % 5)) -eq 0 ]; then
        echo "Still waiting... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    fi
    sleep 2
done

if [ $HEALTHY -eq 0 ]; then
    echo -e "${RED}❌ App did not become healthy after $MAX_ATTEMPTS attempts${NC}"
    echo "Check logs with: docker compose -f docker-compose.fly.yml logs"
    exit 1
fi

echo ""
echo "Running tests..."
echo ""

# Test 1: Health endpoint
echo "Test 1: Health endpoint"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "   Response: $HEALTH_RESPONSE"
    exit 1
fi

echo ""

# Test 2: Homepage
echo "Test 2: Homepage"
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Homepage loads${NC}"
else
    echo -e "${RED}❌ Homepage failed${NC}"
    exit 1
fi

echo ""

# Test 3: Chat endpoint (may fail if RAG not initialized yet)
echo "Test 3: Chat endpoint"
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"question": "What is the party position on healthcare?"}')

if echo "$CHAT_RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✅ Chat endpoint works${NC}"
    echo "   Response preview: $(echo "$CHAT_RESPONSE" | head -c 100)..."
elif echo "$CHAT_RESPONSE" | grep -q "initializing"; then
    echo -e "${YELLOW}⚠️  Chat endpoint responded but RAG is still initializing${NC}"
    echo "   This is normal on first startup. Wait a few minutes and try again."
else
    echo -e "${RED}❌ Chat endpoint failed${NC}"
    echo "   Response: $CHAT_RESPONSE"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Your app is ready at: http://localhost:8000"
echo ""
echo "To view logs: docker compose -f docker-compose.fly.yml logs -f"
echo "To stop: docker compose -f docker-compose.fly.yml down"

