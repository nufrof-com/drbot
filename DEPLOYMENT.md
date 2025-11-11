# Deployment Guide

This guide covers deploying the Democratic Republican SpokesBot to production with cost protection and automated deployments.

## Recommended: Fly.io Deployment

Fly.io is recommended because:
- ✅ Built-in DDoS protection
- ✅ Automatic HTTPS
- ✅ GitHub integration for automated deployments
- ✅ Cost-effective with usage-based pricing
- ✅ Easy scaling controls
- ✅ Supports running Ollama alongside the app

### Prerequisites

1. **Fly.io account**: Sign up at https://fly.io
2. **Fly CLI**: Install from https://fly.io/docs/hands-on/install-flyctl/
3. **GitHub repository**: Your code should be in a GitHub repo

### Step 1: Install Fly CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Or via Homebrew
brew install flyctl

# Verify installation
flyctl version
```

### Step 2: Login to Fly.io

```bash
flyctl auth login
```

### Step 3: Create Fly.io App

**Option A: If you don't have a fly.toml yet:**
```bash
# From your project directory
flyctl launch --no-deploy

# This will:
# - Create a new app
# - Ask you to name it (or use the default)
# - Ask about regions (choose one close to your users)
# - Ask about databases (say no for now)
# - Generate a fly.toml file
```

**Option B: If you already have fly.toml (recommended):**
```bash
# Just create the app without generating a new config
flyctl apps create drp-spokesbot

# Or use a different name
flyctl apps create your-app-name
```

Then edit `fly.toml` and change the `app = "your-app-name"` line to match.

### Step 4: Configure the App

The `fly.toml` file is already configured. You may want to adjust:

- `app = "drp-spokesbot"` - Change to your preferred app name
- `primary_region = "iad"` - Change to your preferred region
- `memory_mb = 2048` - Adjust based on your needs (minimum 2048MB recommended for Ollama)

### Step 5: Deploy

```bash
# Build and deploy (fly.toml already specifies Dockerfile.fly)
flyctl deploy

# If you get errors, try:
flyctl deploy --remote-only
```

**Note**: The first deployment will take longer as it needs to:
1. Build the Docker image
2. Download Ollama models (qwen3:0.6b and qwen3-embedding:0.6b)
3. Initialize the vector database

This can take 5-10 minutes on first deploy.

### Step 6: Set Up Automated Deployments

1. Go to https://fly.io/dashboard
2. Select your app
3. Go to "Settings" → "Secrets"
4. Add any environment variables you need
5. Go to "Settings" → "GitHub Integration"
6. Connect your GitHub repository
7. Enable "Deploy on push"

Now every push to your main branch will automatically deploy!

### Step 7: Monitor and Set Budget Alerts

1. Go to https://fly.io/dashboard
2. Click on your app
3. Go to "Metrics" to monitor usage
4. Set up billing alerts in your Fly.io account settings

### Cost Protection Features

The app includes several cost protection measures:

1. **Rate Limiting**: 10 requests per minute per IP (configurable via `RATE_LIMIT_PER_MINUTE`)
2. **Auto-scaling**: Fly.io can scale to zero when not in use
3. **Request validation**: Questions limited to 1000 characters
4. **Connection limits**: Max 25 concurrent connections per instance

### Adjusting Rate Limits

Edit `fly.toml` or set environment variable:

```bash
flyctl secrets set RATE_LIMIT_PER_MINUTE=5  # More restrictive
flyctl secrets set RATE_LIMIT_PER_MINUTE=20  # More permissive
```

### Scaling

```bash
# Scale to multiple instances for high traffic
flyctl scale count 2

# Scale memory if needed
flyctl scale vm shared-cpu-2x --memory 4096
```

### Monitoring

```bash
# View logs
flyctl logs

# View metrics
flyctl metrics

# SSH into the instance
flyctl ssh console
```

## Alternative: Render Deployment

Render is also a good option with similar features:

1. Sign up at https://render.com
2. Create a new "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. Add environment variables
6. Enable auto-deploy

**Note**: Render requires running Ollama separately or using a cloud LLM service.

## Alternative: Railway Deployment

Railway is easy but can be more expensive:

1. Sign up at https://railway.app
2. Create new project from GitHub
3. Railway will auto-detect the Dockerfile
4. Add environment variables
5. Enable auto-deploy

## Cost Protection Best Practices

1. **Set up billing alerts** on your hosting platform
2. **Monitor usage** regularly in the first few weeks
3. **Start with lower rate limits** (5-10 requests/minute) and increase if needed
4. **Use auto-scaling** to scale down during low traffic
5. **Consider Cloudflare** in front of your app for additional DDoS protection (free tier available)

## Environment Variables

Set these in your deployment platform:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # For single-container deployments
OLLAMA_LLM_MODEL=qwen3:0.6b
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b
PARTY_NAME=Democratic Republicans
BOT_NAME=Democratic Republican SpokesBot
RATE_LIMIT_PER_MINUTE=10
CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
DATA_DIRECTORY=drp_platform/platform
OLLAMA_TEMPERATURE=0.4
```

## Troubleshooting

### Ollama not starting
- Check logs: `flyctl logs` or your platform's log viewer
- Ensure enough memory (minimum 2048MB)
- Verify models are pulled: Check logs for model download

### Rate limiting too strict
- Increase `RATE_LIMIT_PER_MINUTE` in environment variables
- Or adjust in `app/config.py` and redeploy

### High costs
- Check metrics for unusual traffic patterns
- Lower rate limits
- Enable auto-scaling to zero
- Consider using a CDN (Cloudflare) for static assets

## Security Considerations

1. **Rate limiting** is enabled by default
2. **HTTPS** is enforced on Fly.io
3. **Input validation** limits question length
4. **No authentication** - consider adding if needed for admin endpoints
5. **Debug endpoint** (`/chat/debug`) should be disabled in production (add authentication or remove)

