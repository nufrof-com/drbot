# Quick Start Guide - PartyBot

## Option 1: Using Docker Compose (Easiest)

### Step 1: Start the Services
```bash
docker-compose up --build
```

This will:
- Start Ollama service
- Build and start the PartyBot application
- Automatically pull the required models (Qwen3:0.6b and Qwen3-Embedding:0.6b) on first run

**Note**: The first startup may take 5-10 minutes as it downloads the models.

### Step 2: Wait for Initialization
Watch the logs for:
```
Initializing RAG system...
Loaded: sample_platform.txt
Processing 1 documents...
Created X text chunks
Creating vector embeddings...
RAG system initialized successfully!
Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Open the Chat Interface
Open your browser and go to: **http://localhost:8000**

### Step 4: Test It!
Try asking questions like:
- "What is the party's position on healthcare?"
- "What are the Democratic Republicans' views on climate change?"
- "Tell me about education policy"
- "What about economic policy?"

For out-of-scope questions, try:
- "What's the weather today?"
- "Tell me a joke"
- "What's 2+2?"

You should get: "I'm only able to discuss the Democratic Republicans' official positions and policies."

---

## Option 2: Local Development (Without Docker)

### Prerequisites
1. **Install Ollama**: https://ollama.ai
2. **Python 3.11+** installed
3. **Pull the models**:
   ```bash
   ollama pull qwen3:0.6b
   ollama pull qwen3-embedding:0.6b
   ```

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create .env file
```bash
cp .env.example .env
```

Edit `.env` and change:
```
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 3: Start Ollama (if not running)
```bash
ollama serve
```
(Leave this running in a separate terminal)

### Step 4: Run the Application
```bash
# Use poetry run (recommended)
poetry run python -m app.main

# Or activate environment first (Poetry 2.0+)
poetry env activate
python -m app.main
```

### Step 5: Open Browser
Go to: **http://localhost:8000**

---

## Testing the API Directly

You can also test the API using `curl` or any HTTP client:

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","party":"Democratic Republicans"}
```

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the party position on healthcare?"}'
```

Expected response:
```json
{
  "answer": "The Democratic Republicans support universal healthcare access..."
}
```

---

## Troubleshooting

### Models Not Found
- Check Ollama is running: `docker-compose ps` (or `ollama list` locally)
- Check logs: `docker-compose logs ollama`
- Models auto-pull on first use, but this can take time

### No Documents Loaded
- Ensure `.txt` files exist in `data/` directory
- Check application logs for loading errors
- Files must have `.txt` extension

### Port Already in Use
- Change port in `docker-compose.yml` or `.env`
- Or stop the service using port 8000

### Connection Errors
- Ensure Ollama is healthy: `curl http://localhost:11434/api/tags`
- Check network connectivity between containers (Docker) or localhost (local dev)

---

## Adding Your Own Platform Documents

1. Place `.txt` files in the `data/` directory
2. Restart the application
3. The system will automatically:
   - Load the new documents
   - Chunk them
   - Create embeddings
   - Add them to the vector database

**Note**: If you add documents after first startup, you may need to delete `data/chroma_db/` to rebuild the index, or modify the code to handle incremental updates.

---

## Stopping the Services

### Docker Compose
```bash
docker-compose down
```

To also remove volumes (including Ollama models):
```bash
docker-compose down -v
```

### Local Development
Press `Ctrl+C` in the terminal running the app.


