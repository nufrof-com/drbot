"""FastAPI application for Democratic Republican SpokesBot."""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.rag import rag_system
from app.config import settings


async def initialize_rag_background():
    """Initialize RAG system in the background."""
    try:
        print("Starting RAG system initialization in background...")
        # Run the blocking initialization in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, rag_system.initialize)
        print("RAG system initialization completed")
    except Exception as e:
        print(f"WARNING: RAG system initialization failed: {e}")
        print("App will continue to run, but RAG features may not work")
        import traceback
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup - start RAG initialization in background so app can accept connections immediately
    asyncio.create_task(initialize_rag_background())
    print("FastAPI app is ready to accept connections (RAG initializing in background)")
    yield
    # Shutdown (if needed in the future)


app = FastAPI(
    title="Democratic Republican SpokesBot",
    description="A spokesperson chatbot for the Democratic Republican Party platform",
    lifespan=lifespan
)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files (use absolute path)
static_dir = os.path.abspath("static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat UI."""
    html_path = os.path.abspath("static/index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>{settings.bot_name}</h1><p>Chat UI not found. Please ensure static/index.html exists.</p>",
            status_code=404
        )


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """Handle chat requests with rate limiting."""
    if not chat_request.question or not chat_request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Additional validation: limit question length
    if len(chat_request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question is too long. Please keep it under 1000 characters.")
    
    # Check if RAG system is initialized
    if rag_system.vectorstore is None:
        return ChatResponse(
            answer="I'm still initializing. Please wait a moment and try again. The system is loading models and preparing to answer your questions."
        )
    
    try:
        answer = rag_system.query(chat_request.question.strip())
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/chat/debug")
async def chat_debug(request: ChatRequest):
    """Debug endpoint that returns detailed information about the RAG process."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        question = request.question.strip()
        
        # Get detailed information
        doc_type = rag_system._classify_question(question)
        context, retrieved_doc_type = rag_system.retrieve_context(question)
        
        # Generate response
        answer = rag_system.generate_response(question, context, retrieved_doc_type)
        
        return {
            "question": question,
            "classified_as": doc_type,
            "retrieved_doc_type": retrieved_doc_type,
            "context_chunks": context,
            "num_chunks": len(context),
            "answer": answer,
            "context_preview": [chunk[:200] + "..." if len(chunk) > 200 else chunk for chunk in context[:3]]
        }
    except Exception as e:
        return {
            "error": str(e),
            "question": request.question
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "party": settings.party_name}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )

