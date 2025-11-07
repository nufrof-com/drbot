"""Retrieval-Augmented Generation (RAG) functionality for PartyBot."""
import os
import requests
from typing import List, Optional, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
from app.config import settings


class RAGSystem:
    """RAG system for party platform question answering."""
    
    def __init__(self):
        """Initialize the RAG system."""
        self.embeddings = OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vectorstore: Optional[Chroma] = None
        
    def _ensure_ollama_model(self, model_name: str):
        """Ensure Ollama model is available."""
        try:
            response = requests.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                models = [model["name"] for model in response.json().get("models", [])]
                if model_name not in models:
                    print(f"Pulling model {model_name}...")
                    pull_response = requests.post(
                        f"{settings.ollama_base_url}/api/pull",
                        json={"name": model_name},
                        timeout=300
                    )
                    if pull_response.status_code != 200:
                        print(f"Warning: Could not pull model {model_name}")
        except Exception as e:
            print(f"Warning: Could not check/pull model {model_name}: {e}")
    
    def initialize(self):
        """Initialize the RAG system by loading documents and creating embeddings."""
        print("Initializing RAG system...")
        
        # Ensure models are available
        self._ensure_ollama_model(settings.ollama_embedding_model)
        self._ensure_ollama_model(settings.ollama_llm_model)
        
        # Load documents from data directory
        documents = self._load_documents()
        
        if not documents:
            print("Warning: No documents found in data directory")
            return
        
        # Split documents into chunks (preserving metadata)
        print(f"Processing {len(documents)} documents...")
        chunks = []
        for doc in documents:
            doc_chunks = self.text_splitter.split_documents([doc])
            chunks.extend(doc_chunks)
        print(f"Created {len(chunks)} text chunks")
        
        # Create vector store
        print("Creating vector embeddings...")
        # Resolve to absolute path
        chroma_dir = os.path.abspath(settings.chroma_persist_directory)
        os.makedirs(chroma_dir, exist_ok=True)
        
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=chroma_dir
        )
        print("RAG system initialized successfully!")
    
    def _load_documents(self) -> List[Document]:
        """Load text documents from the data directory with metadata."""
        documents = []
        # Resolve to absolute path
        data_dir = os.path.abspath(settings.data_directory)
        
        if not os.path.exists(data_dir):
            print(f"Data directory {data_dir} does not exist")
            return documents
        
        # Define document types based on filename
        history_files = ['democratic_republicans_wikipedia.txt', 'wikipedia.txt']
        platform_files = ['platform.txt']
        
        # Load all .txt files from data directory
        for filename in os.listdir(data_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():
                            # Determine document type
                            if filename in history_files:
                                doc_type = "history"
                            elif filename in platform_files:
                                doc_type = "platform"
                            else:
                                # Default to platform for other files
                                doc_type = "platform"
                            
                            # Create Document with metadata
                            doc = Document(
                                page_content=content,
                                metadata={
                                    "source": filename,
                                    "doc_type": doc_type
                                }
                            )
                            documents.append(doc)
                            print(f"Loaded: {filename} (type: {doc_type})")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return documents
    
    def _classify_question(self, query: str) -> str:
        """
        Classify whether a question is about history, platform, or both.
        
        Returns:
            "history", "platform", or "both"
        """
        query_lower = query.lower()
        
        # History keywords
        history_keywords = [
            'history', 'historical', 'founded', 'founding', 'origins', 'origin',
            'when was', 'when did', 'established', 'early', 'past', 'former',
            'jefferson', 'madison', 'monroe', '1792', '1800', '1824', '1820s',
            'antebellum', 'federalist', 'era', 'period', 'century', 'decade',
            'original party', 'old party', 'early party'
        ]
        
        # Platform keywords
        platform_keywords = [
            'platform', 'policy', 'policies', 'position', 'positions', 'stance',
            'stance on', 'view on', 'views on', 'support', 'oppose', 'advocate',
            'believe', 'current', 'today', 'modern', 'now', 'present', 'contemporary',
            'current party', 'modern party', 'revived party', 'today\'s party'
        ]
        
        # Comparative keywords (indicate need for both)
        comparative_keywords = [
            'differ', 'difference', 'differences', 'compare', 'comparison',
            'versus', 'vs', 'vs.', 'contrast', 'how has', 'how did',
            'changed', 'change', 'evolved', 'evolution', 'then vs', 'then versus',
            'now vs', 'now versus', 'historical vs', 'historical versus',
            'modern vs', 'modern versus', 'old vs', 'old versus'
        ]
        
        # Check for comparative questions
        has_comparative = any(keyword in query_lower for keyword in comparative_keywords)
        
        # Count matches
        history_score = sum(1 for keyword in history_keywords if keyword in query_lower)
        platform_score = sum(1 for keyword in platform_keywords if keyword in query_lower)
        
        # If comparative keywords are present, return "both" (needs both document types)
        # This handles questions like "how does X differ", "compare X and Y", "what changed"
        if has_comparative:
            return "both"
        
        # Also check for explicit mentions of both historical and modern/current
        has_historical_mention = history_score > 0
        has_modern_mention = any(word in query_lower for word in ['modern', 'current', 'now', 'today', 'present', 'revived'])
        
        if has_historical_mention and has_modern_mention:
            return "both"
        
        # If history keywords are present, classify as history
        if history_score > 0 and history_score >= platform_score:
            return "history"
        
        # Default to platform for current party questions
        return "platform"
    
    def retrieve_context(self, query: str, top_k: int = 3) -> Tuple[List[str], str]:
        """
        Retrieve relevant context chunks for a query, filtered by document type.
        
        Returns:
            Tuple of (context_chunks, doc_type)
        """
        if not self.vectorstore:
            return [], "platform"
        
        try:
            # Classify the question
            doc_type = self._classify_question(query)
            
            # If question needs both types, retrieve from both
            if doc_type == "both":
                # Get context from both document types
                history_results = self.vectorstore.similarity_search(
                    query,
                    k=top_k,
                    filter={"doc_type": "history"}
                )
                platform_results = self.vectorstore.similarity_search(
                    query,
                    k=top_k,
                    filter={"doc_type": "platform"}
                )
                
                # Combine results
                all_results = history_results + platform_results
                # Limit to top_k total
                all_results = all_results[:top_k * 2]  # Allow more for comparison
                
                return [doc.page_content for doc in all_results], "both"
            
            # Retrieve with metadata filter for single type
            results = self.vectorstore.similarity_search(
                query,
                k=top_k,
                filter={"doc_type": doc_type}
            )
            
            # If no results with filter, try without filter as fallback
            if not results:
                print(f"Warning: No {doc_type} documents found, searching all documents...")
                results = self.vectorstore.similarity_search(query, k=top_k)
            
            return [doc.page_content for doc in results], doc_type
        except Exception as e:
            print(f"Error retrieving context: {e}")
            # Fallback to unfiltered search
            try:
                results = self.vectorstore.similarity_search(query, k=top_k)
                return [doc.page_content for doc in results], "platform"
            except:
                return [], "platform"
    
    def generate_response(self, query: str, context: List[str], doc_type: str) -> str:
        """Generate a response using Ollama LLM."""
        # Construct prompt based on document type
        context_text = "\n\n".join(context) if context else ""
        
        if doc_type == "history":
            prompt = f"""You are a helpful assistant that answers questions about the historical Democratic-Republican Party (1792-1824).

Use the following context from historical documents about the party to answer the question. If the question cannot be answered using this context, or if it's about topics outside the party's history, respond with: "I'm only able to discuss the historical Democratic-Republican Party (1792-1824)."

Context from historical documents:
{context_text}

Question: {query}

Answer:"""
        elif doc_type == "both":
            # Separate context by document type if possible
            # For now, provide all context and let the model distinguish
            prompt = f"""You are a helpful assistant that answers questions comparing the historical Democratic-Republican Party (1792-1824) and the modern {settings.party_name} party.

The following context contains information from both historical documents about the original party and modern platform documents about the current party. Use this context to compare and contrast the historical and modern positions.

Context (may include both historical and modern information):
{context_text}

Question: {query}

Answer by comparing the historical Democratic-Republican Party positions with the modern {settings.party_name} platform. If you cannot find sufficient information to make a comparison, indicate what information is missing."""
        else:  # platform
            prompt = f"""You are a helpful assistant that answers questions about the {settings.party_name}'s official platform and policies.

Use the following context from the party's official platform documents to answer the question. If the question cannot be answered using this context, or if it's about topics outside the party's platform, respond with: "I'm only able to discuss the {settings.party_name}'s official positions and policies."

Context from party platform documents:
{context_text}

Question: {query}

Answer:"""
        
        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_llm_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "I apologize, but I couldn't generate a response.")
            else:
                return f"Error: Could not generate response (status {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def query(self, user_question: str) -> str:
        """Process a user question and return a response."""
        # Retrieve relevant context (filtered by document type)
        context, doc_type = self.retrieve_context(user_question)
        
        # Generate response
        response = self.generate_response(user_question, context, doc_type)
        
        return response


# Global RAG instance
rag_system = RAGSystem()

