# Troubleshooting Guide

## Common Errors and Solutions

### Poetry/pyproject.toml Errors

#### Error: "pyproject.toml changed significantly since poetry.lock was last generated"

**Solution:**
```bash
rm poetry.lock
poetry lock
poetry install
```

#### Error: Poetry warnings about deprecated fields

If you see warnings about `[tool.poetry.name]` being deprecated, these are just warnings and won't prevent the project from working. The current `pyproject.toml` is compatible with Poetry 2.x.

### Ollama Errors

#### Error: "address already in use" when running `ollama serve`

This means Ollama is already running. You don't need to run `ollama serve` manually if Ollama is installed as a service.

**Solution:**
```bash
# Check if Ollama is already running
curl http://localhost:11434/api/tags

# If it works, Ollama is already running - you don't need to start it manually
# If it doesn't work, check if Ollama is running as a service:
# macOS: Check Activity Monitor or run: ps aux | grep ollama
# Linux: systemctl status ollama
```

#### Error: "connection refused" when accessing Ollama

**Solution:**
1. Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. If not running, start it:
   ```bash
   # macOS: Usually runs as a service automatically
   # If not, run: ollama serve
   
   # Linux: 
   sudo systemctl start ollama
   # Or: ollama serve
   ```

#### Error: Model not found

**Solution:**
```bash
# Pull the required models
ollama pull qwen3:0.6b
ollama pull qwen3-embedding:0.6b

# Verify they're installed
ollama list
```

### Python/pyenv Errors

#### Error: "pyenv: command not found"

**Solution:**
1. Install pyenv: https://github.com/pyenv/pyenv#installation
2. Add to your shell config (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export PYENV_ROOT="$HOME/.pyenv"
   [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   ```
3. Restart your terminal or run: `source ~/.zshrc`

#### Error: Poetry can't find Python 3.11

**Solution:**
```bash
# Install Python 3.11 via pyenv
pyenv install 3.11
pyenv local 3.11

# Tell Poetry to use it
poetry env use $(pyenv which python)

# Verify
poetry env info
```

### Application Errors

#### Error: "No documents found in data directory"

**Solution:**
1. Ensure `.txt` files exist in the `data/` directory
2. Check file permissions: `ls -la data/`
3. Verify the path in logs - it should show the absolute path

#### Error: ChromaDB permission errors

**Solution:**
```bash
# Remove the old database and restart
rm -rf data/chroma_db/
# Then restart the application
```

#### Error: "Module not found" errors

**Solution:**
```bash
# Use poetry run (recommended)
poetry run python -m app.main

# Or activate the environment (Poetry 2.0+)
poetry env activate
python -m app.main

# If dependencies are missing:
poetry install
```

### Port Conflicts

#### Error: "Address already in use" on port 8000

**Solution:**
1. Find what's using the port:
   ```bash
   lsof -i :8000
   # Or on Linux: netstat -tulpn | grep 8000
   ```
2. Kill the process or change the port in `.env`:
   ```
   APP_PORT=8001
   ```

## Quick Diagnostic Commands

```bash
# Check Python version
pyenv version

# Check Poetry
poetry --version
poetry env info

# Check Ollama
ollama --version
ollama list
curl http://localhost:11434/api/tags

# Check if app can start
poetry run python -c "from app.main import app; print('OK')"
```

## Getting Help

If you're still experiencing issues:

1. Check the application logs for detailed error messages
2. Verify all prerequisites are installed and configured
3. Ensure you're using the correct Python version (3.11)
4. Make sure Ollama is running and accessible
5. Verify your `.env` file has the correct `OLLAMA_BASE_URL`

