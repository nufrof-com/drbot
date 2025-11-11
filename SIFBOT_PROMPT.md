# Prompt for Creating SIFBot (Code Analysis RAG System)

Create a Python-based chatbot called **SIFBot** that answers questions about a codebase for Idaho SIF developers. The chatbot should use **Qwen3:1.5b** (or larger, up to 2b) as the local LLM and **Qwen3-Embedding:1.5b** (or equivalent) as the embedding model via Ollama. It needs to include Retrieval-Augmented Generation (RAG) with **ChromaDB** for code understanding and business logic extraction.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) system that:
- Parses a large codebase (~750k lines) and extracts code functions, classes, and business logic
- Stores code chunks in a vector database (ChromaDB) with metadata
- Allows developers to ask natural language questions about the codebase
- Uses local LLMs via Ollama to answer questions based on retrieved code context

## Key Requirements

1. **Platform**: Windows (use Windows-specific setup instructions)
2. **Purpose**: Code analysis and business logic understanding
3. **Data Source**: Code files from a codebase (~750k lines), not text documents
4. **Model Size**: Use larger models (1.5b-2b) since we have 64GB RAM
5. **Document Processing**: Need to iterate through code files and extract meaningful chunks
6. **Question Types**: Focus on "what does this do?", "how does X work?", "what's the business logic for Y?"

## Project Requirements

### Core Features
- **Local LLM**: Uses Qwen3:1.5b (or 2b) via Ollama for code question answering
- **Embeddings**: Uses Qwen3-Embedding:1.5b (or equivalent) for code embeddings
- **RAG System**: Retrieves relevant code snippets and documentation
- **Code Parser**: Script to iterate through codebase and extract code with context
- **FastAPI Backend**: Modern Python web framework
- **Simple Web UI**: Clean chat interface
- **Windows Support**: Setup instructions for Windows (PowerShell, etc.)

### Tech Stack
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **RAG**: LangChain, ChromaDB
- **LLM**: Ollama (Qwen3:1.5b or 2b)
- **Code Processing**: Custom script to parse code files
- **Frontend**: HTML, JavaScript, Tailwind CSS

### Project Structure
```
sifbot/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── rag.py           # RAG system for code
│   └── config.py         # Configuration
├── scripts/
│   ├── parse_codebase.py  # Script to iterate through code and populate DB
│   └── test_questions.py  # Test script
├── static/
│   └── index.html       # Chat UI
├── data/
│   ├── code_chunks/     # Processed code chunks (optional, for debugging)
│   └── chroma_db/       # Vector database (auto-generated)
├── pyproject.toml
├── .python-version
├── .env.example
└── README.md
```

### Code Parsing Script Requirements

Create `scripts/parse_codebase.py` that:

1. **Iterates through codebase**:
   - Walks directory tree
   - Identifies code files by extension (.py, .js, .ts, .java, .cs, .go, .rs, etc.)
   - Skips common ignore patterns (node_modules, .git, __pycache__, etc.)

2. **Extracts code with context**:
   - For each file, extract:
     - File path and name
     - Function/class definitions with their code
     - Comments and docstrings
     - Imports and dependencies
   - Preserve code structure and relationships

3. **Chunking strategy for code**:
   - Chunk by function/class (preferred) - each function/class is a chunk
   - Include surrounding context (file path, imports, class context)
   - For large functions, split intelligently
   - Preserve metadata: file_path, language, function_name, class_name, line_numbers

4. **Metadata for routing**:
   - `file_type`: language (python, javascript, typescript, etc.)
   - `component_type`: frontend, backend, database, config, etc.
   - `file_path`: full path for reference
   - `function_name`: if it's a function
   - `class_name`: if it's a class method

### RAG System Requirements

1. **Document Classification**:
   - Classify questions by intent:
     - **Function/Class questions**: "What does function X do?", "How does class Y work?"
     - **Business Logic questions**: "How does authentication work?", "What's the payment flow?"
     - **Architecture questions**: "What's the overall structure?", "How are components connected?"
     - **File/Module questions**: "What does file X do?", "What's in module Y?"

2. **Context Retrieval**:
   - Retrieve relevant code chunks based on:
     - Function/class names mentioned
     - Keywords in question
     - File paths mentioned
     - Related code (functions that call each other)

3. **Response Generation**:
   - Use prompts tailored for code understanding
   - Explain what code does in plain language
   - Reference file paths and line numbers
   - Explain business logic and data flow

### Configuration

Environment variables:
- `OLLAMA_BASE_URL`: Ollama API URL (default: `http://localhost:11434`)
- `OLLAMA_LLM_MODEL`: LLM model (default: `qwen3:1.5b` or `qwen3:2b`)
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (default: `qwen3-embedding:1.5b`)
- `CODEBASE_ROOT`: Root directory of codebase to analyze
- `CHROMA_PERSIST_DIRECTORY`: Path to store ChromaDB data
- `APP_HOST`: Application host (default: `0.0.0.0`)
- `APP_PORT`: Application port (default: `8000`)

### Windows-Specific Setup

1. **Python Installation**:
   - Use pyenv-win or direct Python installer
   - Or use Poetry's built-in Python management

2. **Poetry Installation**:
   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

3. **Ollama Installation**:
   - Download from https://ollama.ai
   - Install Windows version
   - Runs as service or manually with `ollama serve`

4. **Path Setup**:
   - Add Poetry to PATH if needed
   - Use PowerShell or Git Bash for commands

### Code Parsing Example

The `parse_codebase.py` script should:
- Accept a root directory path
- Walk through all code files
- Extract functions, classes, and their docstrings
- Create chunks with metadata
- Store in ChromaDB with proper metadata for filtering

Example chunk structure:
```python
{
    "content": "def process_payment(amount, user_id):\n    # Business logic for payment processing\n    ...",
    "metadata": {
        "file_path": "src/payment/processor.py",
        "language": "python",
        "function_name": "process_payment",
        "class_name": None,
        "component_type": "backend",
        "line_start": 45,
        "line_end": 78
    }
}
```

### Prompt Engineering for Code

The prompts should:
- Ask the model to explain code in business terms
- Focus on "what" and "why" not just "how"
- Reference file locations
- Explain data flow and business logic
- Handle questions like:
  - "What does this function do?"
  - "How does authentication work in this codebase?"
  - "What's the business logic for processing payments?"
  - "Where is the user registration handled?"

### Performance Considerations

- For 750k lines, use efficient chunking (by function/class)
- Consider indexing strategy (maybe index by component type)
- Use appropriate chunk size (500-1000 tokens for code)
- Consider incremental updates (only re-index changed files)

### Testing

Include test questions like:
- "What does the authentication system do?"
- "How does user registration work?"
- "What's the main entry point of the application?"
- "Where is the payment processing logic?"
- "What database models are used?"

## Implementation Notes

1. **Architecture**: FastAPI backend with RAG system using LangChain and ChromaDB
2. **Use tree-sitter or similar** for better code parsing (optional enhancement)
3. **Support multiple languages** - detect and parse appropriately
4. **Handle large codebases** - efficient indexing and retrieval
5. **Windows paths** - use `pathlib` for cross-platform compatibility
6. **Model selection** - with 64GB RAM, can use 1.5b-2b models comfortably
7. **Similar to document Q&A systems** but adapted for code analysis instead of text documents

## Deliverables

1. Complete project structure
2. Code parsing script (`scripts/parse_codebase.py`)
3. RAG system adapted for code (`app/rag.py`)
4. FastAPI backend with code-focused endpoints
5. Web UI for asking code questions
6. Windows setup instructions in README
7. Configuration files (pyproject.toml, .env.example)
8. Documentation on how to index a codebase

## Example Usage

```bash
# 1. Parse the codebase
poetry run python scripts/parse_codebase.py --root C:\path\to\codebase

# 2. Start the application
poetry run python -m app.main

# 3. Ask questions
# "What does the authentication module do?"
# "How does payment processing work?"
# "Where is the user model defined?"
```

---

## Architecture Pattern

This follows a standard RAG (Retrieval-Augmented Generation) pattern:
1. **Ingestion**: Parse codebase → Extract code chunks → Generate embeddings → Store in vector DB
2. **Query**: User question → Embed question → Retrieve similar code chunks → Generate answer with context
3. **Similar to**: Document Q&A systems, but adapted for code instead of text documents

The system should be similar to how a document-based Q&A chatbot works, but:
- Instead of loading text files, it parses code files
- Instead of chunking by paragraphs, it chunks by functions/classes
- Instead of answering policy questions, it explains code and business logic
- Metadata includes file paths, languages, function names instead of document types

