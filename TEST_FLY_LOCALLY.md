# Testing Fly.io Deployment Locally

This guide shows you how to test the Fly.io deployment configuration locally using Docker, so you can verify everything works before deploying.

## Quick Start

```bash
# Build and run the container (matches Fly.io environment exactly)
# Note: Use 'docker compose' (space) for Docker Desktop, or 'docker-compose' (hyphen) for standalone
docker compose -f docker-compose.fly.yml up --build

# Or run in detached mode
docker compose -f docker-compose.fly.yml up --build -d

# View logs
docker compose -f docker-compose.fly.yml logs -f

# Stop the container
docker compose -f docker-compose.fly.yml down
```

**Note**: If you get "command not found", try:
- `docker compose` (space) - for Docker Desktop (newer)
- `docker-compose` (hyphen) - for standalone docker-compose (older)

## What This Tests

This setup uses `Dockerfile.fly`, which is the exact same Dockerfile used in Fly.io deployment. It:

- ✅ Uses the same base image (`ollama/ollama:latest`)
- ✅ Installs Python the same way
- ✅ Runs Ollama and FastAPI in the same container (like Fly.io)
- ✅ Uses the same startup script
- ✅ Tests the same environment variables

## First Run

The first time you run this, it will:

1. **Build the Docker image** (takes 2-3 minutes)
2. **Start Ollama** inside the container
3. **Download models** (`qwen3:0.6b` and `qwen3-embedding:0.6b`) - this can take 5-10 minutes
4. **Initialize RAG system** - creates embeddings (takes 1-2 minutes)
5. **Start FastAPI** - app becomes available at http://localhost:8000

**Total first-run time: ~10-15 minutes**

Subsequent runs will be much faster since models are cached in the Docker volume.

## Accessing the App

Once the container is running:

- **Web UI**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API**: http://localhost:8000/chat

## Monitoring

### View Logs
```bash
# Follow all logs
docker compose -f docker-compose.fly.yml logs -f

# Follow just the app logs
docker compose -f docker-compose.fly.yml logs -f drp-spokesbot
```

### Check Container Status
```bash
docker compose -f docker-compose.fly.yml ps
```

### Check Health
```bash
curl http://localhost:8000/health
```

### Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the party position on healthcare?"}'
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker compose -f docker-compose.fly.yml logs

# Rebuild from scratch
docker compose -f docker-compose.fly.yml down -v
docker compose -f docker-compose.fly.yml build --no-cache
docker compose -f docker-compose.fly.yml up
```

### Models Not Downloading
- Check your internet connection
- Models are large (~600MB total), so download may take time
- Check logs: `docker compose -f docker-compose.fly.yml logs | grep -i "pull"`

### Port Already in Use
If port 8000 is already in use:
```bash
# Change the port mapping in docker-compose.fly.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Clear Everything and Start Fresh
```bash
# Stop and remove everything including volumes
docker compose -f docker-compose.fly.yml down -v

# Remove the built image
docker rmi partybot-drp-spokesbot

# Rebuild and start
docker compose -f docker-compose.fly.yml up --build
```

## Differences from Fly.io

While this setup closely matches Fly.io, there are a few differences:

1. **Networking**: Fly.io uses its own internal networking, but Docker uses bridge networking
2. **Scaling**: This runs a single container, Fly.io can scale to multiple machines
3. **Auto-scaling**: Fly.io can auto-stop/start machines, this container runs continuously
4. **Volumes**: Local volumes vs Fly.io's persistent volumes

## Next Steps

Once you've verified everything works locally:

1. **Deploy to Fly.io**:
   ```bash
   flyctl deploy
   ```

2. **Monitor deployment**:
   ```bash
   flyctl logs
   flyctl status
   ```

3. **Access your app**:
   ```bash
   flyctl open
   ```

