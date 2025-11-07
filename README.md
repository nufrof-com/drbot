# PartyBot

A Python-based chatbot that answers questions about a political party's official platform using Retrieval-Augmented Generation (RAG) with local LLMs via Ollama.

## Features

- **Local LLM**: Uses Qwen3:0.6b via Ollama for question answering
- **Embeddings**: Uses Qwen3-Embedding:0.6b for document embeddings
- **RAG System**: Retrieves relevant context from party platform documents
- **FastAPI Backend**: Modern Python web framework
- **Simple Web UI**: Clean chat interface with Tailwind CSS
- **Docker Support**: Easy deployment with Docker Compose
- **Cloud Ready**: Deployable to Render, Fly.io, Railway, etc.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **RAG**: LangChain, ChromaDB
- **LLM**: Ollama (Qwen3:0.6b)
- **Frontend**: HTML, JavaScript, Tailwind CSS

## Quick Start

### Prerequisites

- **Python 3.11+** (managed via pyenv)
- **Poetry** for dependency management  
- **Ollama** for running local LLMs (install from https://ollama.ai)
- (Optional) Docker and Docker Compose for containerized deployment

### Development Setup (Recommended)

1. **Clone and navigate to the project**:
   ```bash
   cd partybot
   ```

2. **Install Python version using pyenv**:
   ```bash
   pyenv install 3.11
   pyenv local 3.11
   ```

3. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # Or: pip install poetry
   ```

4. **Install dependencies with Poetry**:
   ```bash
   poetry install
   ```
   This will create a virtual environment and install all dependencies.

5. **Activate the Poetry environment** (Poetry 2.0+):
   ```bash
   poetry env activate
   ```
   Or run commands with `poetry run` prefix (recommended):
   ```bash
   poetry run python -m app.main
   ```

6. **Install and start Ollama**:
   ```bash
   # Install Ollama from https://ollama.ai if not already installed
   # Start Ollama service
   ollama serve
   ```
   Keep this running in a separate terminal.

7. **Pull required models** (in a new terminal):
   ```bash
   ollama pull qwen3:0.6b
   ollama pull qwen3-embedding:0.6b
   ```

8. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and ensure:
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   ```

9. **Add your party platform documents**:
   - Place `.txt` files in the `data/` directory
   - **Document routing**: The system automatically routes questions:
     - `platform.txt` - Used for questions about the current party's platform and policies
     - `democratic_republicans_wikipedia.txt` - Used for historical questions about the original party (1792-1824)
   - Other `.txt` files default to "platform" type
   - These will be loaded and embedded on startup

10. **Run the application**:
    ```bash
    poetry run python -m app.main
    ```
    Or if you've activated the environment with `poetry env activate`:
    ```bash
    python -m app.main
    ```

11. **Access the application**:
    - Open http://localhost:8000 in your browser
    - The first startup may take a few minutes as it processes documents and creates embeddings

12. **Test the system** (optional):
    ```bash
    # Run test questions to verify everything works
    poetry run python scripts/test_questions.py
    ```

### Using Docker Compose (Alternative)

1. **Start the services**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   - Open http://localhost:8000 in your browser
   - The first startup may take a few minutes as Ollama downloads the models

## Project Structure

```
partybot/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── rag.py           # RAG system implementation
│   └── config.py        # Configuration management
├── static/
│   └── index.html       # Chat UI
├── data/
│   └── *.txt           # Party platform documents
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml       # Poetry configuration
├── .python-version      # pyenv Python version
├── requirements.txt     # Legacy pip requirements (use Poetry)
├── .env.example
└── README.md
```

## Configuration

Environment variables (set in `.env` or docker-compose.yml):

- `OLLAMA_BASE_URL`: Ollama API URL (default: `http://ollama:11434`)
- `OLLAMA_LLM_MODEL`: LLM model name (default: `qwen3:0.6b`)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model name (default: `qwen3-embedding:0.6b`)
- `PARTY_NAME`: Name of the political party (default: `Democratic Republicans`)
- `CHROMA_PERSIST_DIRECTORY`: Path to store ChromaDB data
- `APP_HOST`: Application host (default: `0.0.0.0`)
- `APP_PORT`: Application port (default: `8000`)

## API Endpoints

### `GET /`
Serves the chat UI.

### `POST /chat`
Processes a chat question.

**Request**:
```json
{
  "question": "What is the party's position on healthcare?"
}
```

**Response**:
```json
{
  "answer": "The Democratic Republicans support universal healthcare access..."
}
```

### `GET /health`
Health check endpoint.

### `POST /chat/debug`
Debug endpoint that returns detailed information about the RAG process.

**Request**:
```json
{
  "question": "Would the party lower minimum wage?"
}
```

**Response**:
```json
{
  "question": "Would the party lower minimum wage?",
  "classification": "platform",
  "context_chunks": 5,
  "context_preview": ["...", "..."],
  "answer": "The Democratic Republicans would not lower minimum wage..."
}
```

## Deployment

### Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `poetry install --no-dev && poetry run pip install -r requirements.txt` (or use Poetry directly)
4. Set start command: `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. **Note**: You'll need to run Ollama separately or use a service that supports it

### Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Create `fly.toml`:
   ```toml
   app = "partybot"
   primary_region = "iad"
   
   [build]
     dockerfile = "Dockerfile"
   
   [[services]]
     internal_port = 8000
     protocol = "tcp"
   ```
3. Deploy: `fly deploy`
4. **Note**: Consider using Fly.io's volume support for ChromaDB persistence

### Railway

1. Connect your GitHub repository
2. Railway will auto-detect the Dockerfile
3. Add environment variables
4. Deploy

**Important**: For cloud deployment, you may need to:
- Run Ollama as a separate service
- Use a managed vector database (e.g., Pinecone, Weaviate) instead of ChromaDB
- Adjust the architecture for cloud constraints

## How It Works

1. **Startup**: 
   - Loads text documents from `/data`
   - Classifies documents by type (history vs platform) based on filename
   - Chunks documents into smaller pieces (preserving metadata)
   - Generates embeddings using Ollama
   - Stores vectors in ChromaDB with document type metadata

2. **Query Processing**:
   - User submits a question
   - System classifies question intent (history vs platform) using keyword matching
   - System embeds the question
   - Retrieves top-k relevant document chunks **filtered by document type**
   - Constructs a prompt with context (tailored to history or platform)
   - Queries Ollama LLM for response
   - Returns answer to user

3. **Document Routing**:
   - **History questions** (keywords: history, founded, where, when, Jefferson, 1792, etc.) → Uses `democratic_republicans_wikipedia.txt`
   - **Platform questions** (keywords: platform, policy, position, current, etc.) → Uses `platform.txt`
   - **Comparative questions** (keywords: differ, compare, changed, revived, etc.) → Uses both documents
   - Defaults to platform if unclear
   
   **Note**: The modern Democratic Republicans is a revival of the historical party. Questions about "revived" or "revival" will compare historical vs modern positions.

4. **Out-of-Scope Handling**:
   - History questions: "I'm only able to discuss the historical Democratic-Republican Party (1792-1824)."
   - Platform questions: "I'm only able to discuss the [Party Name]'s official positions and policies."

## Troubleshooting

### Models not found
- Ensure Ollama is running: `docker-compose ps`
- Check Ollama logs: `docker-compose logs ollama`
- Models will be auto-pulled on first use, but this may take time

### No documents loaded
- Ensure `.txt` files exist in `data/` directory
- Check application logs for loading errors

### ChromaDB errors
- Ensure write permissions for `data/chroma_db/`
- Try deleting `chroma_db/` and restarting to rebuild the vector database
- If you add new documents, delete `data/chroma_db/` to force a rebuild

### Poetry/pyenv issues
- Ensure pyenv is properly initialized in your shell: `eval "$(pyenv init -)"`
- Verify Python version: `pyenv version` (should show 3.11)
- If Poetry can't find Python: `poetry env use $(pyenv which python)`
- To see Poetry environment info: `poetry env info`
- If you see "pyproject.toml changed significantly" error: `rm poetry.lock && poetry lock`

### Ollama serve errors
- **"Address already in use"**: Ollama is already running. Check with `curl http://localhost:11434/api/tags`
- **"Connection refused"**: Start Ollama with `ollama serve` (or it may run as a service automatically)
- **Model not found**: Pull models with `ollama pull qwen3:0.6b` and `ollama pull qwen3-embedding:0.6b`
- See `TROUBLESHOOTING.md` for more detailed solutions

## Development

### Adding Dependencies

```bash
poetry add package-name
poetry add --group dev package-name  # for dev dependencies
```

### Running Commands

```bash
# Option 1: Use poetry run (recommended)
poetry run python -m app.main
poetry run pytest  # if tests are added

# Option 2: Activate environment (Poetry 2.0+)
poetry env activate
python -m app.main
```

### Updating Dependencies

```bash
poetry update
```

### Scraping Wikipedia Content

A script is provided to scrape Wikipedia entries and add them to the data directory:

```bash
# Scrape the Democratic-Republican Party Wikipedia page
poetry run python scripts/scrape_wikipedia.py
```

This will:
- Fetch the Wikipedia page content
- Clean and format the text
- Save it to `data/democratic_republicans_wikipedia.txt`
- The RAG system will automatically load it on next startup

To scrape a different Wikipedia page, edit `scripts/scrape_wikipedia.py` and change the `page_title` variable.

**Note**: After adding new documents, you may need to delete `data/chroma_db/` and restart the application to rebuild the vector database.

### Testing and Debugging

#### Test Questions Script

Run comprehensive tests to verify the RAG system is working correctly:

```bash
# Run all test questions
poetry run python scripts/test_questions.py

# Test a specific question
poetry run python scripts/test_questions.py "Where was the party founded?"
```

The script will:
- Test various question types (negative, history, platform, comparative)
- Show classification results
- Display retrieved context chunks
- Show generated answers
- Provide a summary of classification accuracy

#### Debug API Endpoint

For detailed debugging information, use the `/chat/debug` endpoint:

```bash
curl -X POST http://localhost:8000/chat/debug \
  -H "Content-Type: application/json" \
  -d '{"question": "Would the party lower minimum wage?"}'
```

This returns:
- Question classification
- Retrieved context chunks
- Number of chunks
- Full answer
- Context previews

## Quick Reference

### Starting the Application

```bash
# 1. Ensure Ollama is running (usually runs automatically on macOS)
curl http://localhost:11434/api/tags  # Verify it's running

# 2. Start the application
poetry run python -m app.main

# 3. Open browser
# http://localhost:8000
```

### Rebuilding the Vector Database

If you add new documents or want to rebuild:

```bash
# Delete the old database
rm -rf data/chroma_db/

# Restart the application (it will rebuild automatically)
poetry run python -m app.main
```

### File Structure

- `data/platform.txt` - Modern party platform (used for current policy questions)
- `data/democratic_republicans_wikipedia.txt` - Historical party info (used for history questions)
- `data/chroma_db/` - Vector database (auto-generated, can be deleted to rebuild)

### Common Commands

```bash
# Test questions
poetry run python scripts/test_questions.py

# Scrape Wikipedia
poetry run python scripts/scrape_wikipedia.py

# Check health
curl http://localhost:8000/health

# Debug a question
curl -X POST http://localhost:8000/chat/debug \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here"}'
```

## License

MIT

