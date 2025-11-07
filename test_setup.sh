#!/bin/bash
# Quick setup and test script for PartyBot

echo "🚀 PartyBot Setup & Test Script"
echo "================================"
echo ""

# Check if Ollama is running
echo "1. Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama is running"
else
    echo "   ⚠️  Ollama is not running. Starting it..."
    echo "   Please run 'ollama serve' in another terminal, then press Enter"
    read
fi

# Check if models are available
echo ""
echo "2. Checking for required models..."
if ollama list | grep -q "qwen3:0.6b"; then
    echo "   ✅ qwen3:0.6b is available"
else
    echo "   📥 Pulling qwen3:0.6b (this may take a few minutes)..."
    ollama pull qwen3:0.6b
fi

if ollama list | grep -q "qwen3-embedding:0.6b"; then
    echo "   ✅ qwen3-embedding:0.6b is available"
else
    echo "   📥 Pulling qwen3-embedding:0.6b (this may take a few minutes)..."
    ollama pull qwen3-embedding:0.6b
fi

# Check pyenv
echo ""
echo "3. Checking pyenv and Python version..."
if command -v pyenv &> /dev/null; then
    if pyenv version-name | grep -q "3.11"; then
        echo "   ✅ Python 3.11 is active via pyenv"
    else
        echo "   📥 Installing Python 3.11 via pyenv..."
        pyenv install 3.11
        pyenv local 3.11
        echo "   ✅ Python 3.11 installed and set as local"
    fi
else
    echo "   ⚠️  pyenv not found. Please install pyenv first."
    echo "   Visit: https://github.com/pyenv/pyenv#installation"
fi

# Check Poetry
echo ""
echo "4. Checking Poetry..."
if command -v poetry &> /dev/null; then
    echo "   ✅ Poetry is installed"
else
    echo "   📥 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "   ⚠️  Please restart your terminal or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# Install dependencies with Poetry
echo ""
echo "5. Installing dependencies with Poetry..."
if [ -f "poetry.lock" ]; then
    echo "   📦 Installing from lock file..."
    poetry install
else
    echo "   📦 Installing dependencies (this may take a few minutes)..."
    poetry install
fi

# Check .env file
echo ""
echo "6. Checking configuration..."
if [ -f .env ]; then
    echo "   ✅ .env file exists"
else
    echo "   📝 Creating .env file from .env.example..."
    cp .env.example .env
    # Update for local development
    sed -i '' 's|OLLAMA_BASE_URL=http://ollama:11434|OLLAMA_BASE_URL=http://localhost:11434|' .env
    echo "   ✅ Created .env file (updated for local development)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Make sure Ollama is running: ollama serve"
echo "2. Start the app: poetry run python -m app.main"
echo "   (Or activate environment: poetry env activate, then: python -m app.main)"
echo "3. Open http://localhost:8000 in your browser"
echo ""


