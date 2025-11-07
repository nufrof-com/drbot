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
        # Use smaller chunks for small documents, larger for big ones
        # This will be adjusted per document in the splitting process
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Better separators
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
            # Adjust chunk size based on document length
            doc_length = len(doc.page_content)
            if doc_length < 2000:
                # Small documents: keep as single chunk or minimal splitting
                if doc_length < 1000:
                    # Very small - keep as one chunk
                    chunks.append(doc)
                else:
                    # Small but might need splitting - use smaller chunks
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=doc_length + 100,  # Slightly larger than doc
                        chunk_overlap=0,
                        length_function=len,
                    )
                    doc_chunks = splitter.split_documents([doc])
                    chunks.extend(doc_chunks)
            else:
                # Large documents: use normal splitting
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
        
        # History keywords - check for origin/founding questions first
        origin_phrases = [
            'where did', 'where was', 'where came', 'come from', 'came from',
            'where originate', 'where start', 'where begin', 'where founded',
            'where established', 'where created', 'where formed'
        ]
        
        # Check for "where" questions about founding/origin (definitely history)
        if any(phrase in query_lower for phrase in origin_phrases):
            return "history"
        
        # Check for "when" questions about founding (definitely history)
        when_founding_phrases = [
            'when was', 'when did', 'when started', 'when began',
            'when founded', 'when established', 'when created', 'when formed'
        ]
        if any(phrase in query_lower for phrase in when_founding_phrases):
            return "history"
        
        # Check for "now when, where" or similar follow-ups asking for both time and place
        # These are typically asking for historical founding details
        if 'now when' in query_lower or ('when' in query_lower and 'where' in query_lower):
            return "history"
        
        # Standalone "where" questions are likely asking about location/origin (history)
        if query_lower.strip() == 'where' or query_lower.startswith('where'):
            # Check if it's asking about the party (implicit from context)
            if 'party' in query_lower or len(query_lower.split()) <= 3:
                return "history"
        
        history_keywords = [
            'history', 'historical', 'founded', 'founding', 'origins', 'origin',
            'established', 'early', 'past', 'former', 'began', 'started',
            'jefferson', 'madison', 'monroe', '1792', '1800', '1824', '1820s',
            'antebellum', 'federalist', 'era', 'period', 'century', 'decade',
            'original party', 'old party', 'early party'
        ]
        
        # Platform keywords
        platform_keywords = [
            'platform', 'policy', 'policies', 'position', 'positions', 'stance',
            'stance on', 'view on', 'views on', 'support', 'oppose', 'advocate',
            'believe', 'current', 'today', 'modern', 'now', 'present', 'contemporary',
            'current party', 'modern party', 'today\'s party'
        ]
        
        # Revival keywords - indicate modern revival, should trigger "both" for comparison
        revival_keywords = [
            'revived', 'revival', 'revive', 'bringing back', 'restart', 'restarted',
            'reestablish', 'reestablishing', 'reformed', 'reform'
        ]
        
        # Comparative keywords (indicate need for both)
        comparative_keywords = [
            'differ', 'difference', 'differences', 'compare', 'comparison',
            'versus', 'vs', 'vs.', 'contrast', 'how has', 'how did',
            'changed', 'change', 'evolved', 'evolution', 'then vs', 'then versus',
            'now vs', 'now versus', 'historical vs', 'historical versus',
            'modern vs', 'modern versus', 'old vs', 'old versus'
        ]
        
        # Check for revival keywords (modern revival of historical party)
        has_revival = any(keyword in query_lower for keyword in revival_keywords)
        
        # Check for comparative questions
        has_comparative = any(keyword in query_lower for keyword in comparative_keywords)
        
        # Count matches
        history_score = sum(1 for keyword in history_keywords if keyword in query_lower)
        platform_score = sum(1 for keyword in platform_keywords if keyword in query_lower)
        
        # If revival keywords are present, it's asking about modern revival vs historical
        # This needs both documents to compare
        if has_revival:
            return "both"
        
        # If comparative keywords are present, return "both" (needs both document types)
        # This handles questions like "how does X differ", "compare X and Y", "what changed"
        if has_comparative:
            return "both"
        
        # Also check for explicit mentions of both historical and modern/current
        has_historical_mention = history_score > 0
        has_modern_mention = any(word in query_lower for word in ['modern', 'current', 'now', 'today', 'present'])
        
        if has_historical_mention and has_modern_mention:
            return "both"
        
        # If history keywords are present, classify as history
        if history_score > 0 and history_score >= platform_score:
            return "history"
        
        # Default to platform for current party questions
        return "platform"
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms to improve retrieval.
        
        For questions about decreasing/lowering something, also search for
        the positive form to find what the party actually supports.
        """
        query_lower = query.lower()
        
        # Map negative terms to positive synonyms for better retrieval
        synonym_map = {
            'lower': ['wage', 'minimum wage', 'raise', 'increase'],
            'decrease': ['wage', 'minimum wage', 'raise', 'increase'],
            'reduce': ['wage', 'minimum wage', 'raise', 'increase'],
            'cut': ['wage', 'minimum wage', 'raise', 'increase'],
        }
        
        # If query contains negative action words, add positive terms
        expanded_terms = [query]
        for negative_term, related_terms in synonym_map.items():
            if negative_term in query_lower:
                for term in related_terms:
                    if term in query_lower:
                        # Add the positive form
                        expanded_terms.append(f"raise {term}")
                        expanded_terms.append(f"increase {term}")
                        expanded_terms.append(f"support {term}")
        
        # Combine original query with expanded terms
        return " ".join(expanded_terms)
    
    def retrieve_context(self, query: str, top_k: int = 5) -> Tuple[List[str], str]:
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
            
            # Expand query for better retrieval
            expanded_query = self._expand_query(query)
            
            # If question needs both types, retrieve from both
            if doc_type == "both":
                # Get context from both document types
                history_results = self.vectorstore.similarity_search(
                    expanded_query,
                    k=top_k,
                    filter={"doc_type": "history"}
                )
                platform_results = self.vectorstore.similarity_search(
                    expanded_query,
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
                expanded_query,
                k=top_k,
                filter={"doc_type": doc_type}
            )
            
            # If no results with filter, try without filter as fallback
            if not results:
                print(f"Warning: No {doc_type} documents found, searching all documents...")
                results = self.vectorstore.similarity_search(expanded_query, k=top_k)
            
            # Also try original query if expanded didn't work well
            if len(results) < 2:
                original_results = self.vectorstore.similarity_search(
                    query,
                    k=top_k,
                    filter={"doc_type": doc_type}
                )
                # Merge and deduplicate by content
                seen_content = set()
                deduplicated = []
                for r in results + original_results:
                    content = r.page_content.strip()
                    if content not in seen_content and len(content) > 50:
                        seen_content.add(content)
                        deduplicated.append(r)
                results = deduplicated
            
            # Remove duplicates and return
            seen_content = set()
            unique_results = []
            for r in results:
                content = r.page_content.strip()
                if content not in seen_content:
                    seen_content.add(content)
                    unique_results.append(r.page_content)
            
            return unique_results, doc_type
        except Exception as e:
            print(f"Error retrieving context: {e}")
            # Fallback to unfiltered search
            try:
                results = self.vectorstore.similarity_search(query, k=top_k)
                return [doc.page_content for doc in results], "platform"
            except:
                return [], "platform"
    
    def _clean_response(self, response: str) -> str:
        """
        Clean up the response to remove formatting markers and meta-commentary.
        """
        # Remove common formatting markers
        response = response.replace("**Answer:**", "")
        response = response.replace("**Answer**:", "")
        response = response.replace("Answer:", "")
        response = response.replace("Answer :", "")
        
        # Remove markdown bold markers that might be at the end
        response = response.replace("**", "")
        
        # Remove meta-commentary patterns (only if the line is primarily meta-commentary)
        lines = response.split('\n')
        cleaned_lines = []
        skip_patterns = [
            "however, the passage does not",
            "leaving this answer as inferred",
            "inferred from the context",
            "the passage does not explicitly",
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            # Only skip lines that are clearly just meta-commentary
            # (contain these patterns and are short/not substantive)
            is_meta = any(pattern in line_lower for pattern in skip_patterns)
            if is_meta and len(line.strip()) < 150:
                continue
            cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines).strip()
        
        # Remove trailing periods and extra whitespace
        response = response.rstrip('. ')
        
        return response
    
    def generate_response(self, query: str, context: List[str], doc_type: str) -> str:
        """Generate a response using Ollama LLM."""
        # Construct prompt based on document type
        context_text = "\n\n".join(context) if context else ""
        
        if doc_type == "history":
            # Check if question is asking about location
            query_lower = query.lower()
            is_location_question = any(word in query_lower for word in ['where', 'location', 'place', 'city', 'state', 'region'])
            is_time_question = any(word in query_lower for word in ['when', 'date', 'year', 'time'])
            
            location_instruction = ""
            if is_location_question:
                location_instruction = " If the question asks 'where', provide the geographical location (city, state, or region), not just dates."
            if is_time_question and is_location_question:
                location_instruction = " If the question asks for both 'when' and 'where', provide both the date/time and the geographical location."
            
            prompt = f"""Answer this question about the historical Democratic-Republican Party (1792-1824) using the information below.

{context_text}

Question: {query}

Provide a clear, direct answer based on the information above.{location_instruction} Do not include formatting markers, labels, or meta-commentary. Just answer the question."""
        elif doc_type == "both":
            prompt = f"""The {settings.party_name} is a modern revival of the historical Democratic-Republican Party (1792-1824). 
Compare the historical party and the modern revived party using the information below.

{context_text}

Question: {query}

Provide a clear comparison between the historical Democratic-Republican Party (1792-1824) and the modern {settings.party_name} party. 
If the question asks about what changed since the party was revived, compare the historical positions with the modern platform.
Do not include formatting markers or meta-commentary. Just answer the question."""
        else:  # platform
            # Check if we have context - if not, the retrieval failed
            if not context_text or len(context_text.strip()) < 50:
                return f"I apologize, but I couldn't find relevant information in the party's platform documents to answer your question. Please try rephrasing your question or ask about a different topic."
            
            # Simple, direct prompt - let the model answer naturally
            prompt = f"""Answer this question about the {settings.party_name}'s platform using the information below.

{context_text}

Question: {query}

Provide a clear, direct answer. Do not include formatting markers, labels like "Answer:", or meta-commentary. Just answer the question naturally."""
        
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
                raw_response = result.get("response", "I apologize, but I couldn't generate a response.")
                # Clean up the response
                cleaned_response = self._clean_response(raw_response)
                return cleaned_response
            else:
                return f"Error: Could not generate response (status {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def query(self, user_question: str, verbose: bool = False) -> str:
        """
        Process a user question and return a response.
        
        Args:
            user_question: The user's question
            verbose: If True, print debug information
        
        Returns:
            The generated response
        """
        # Retrieve relevant context (filtered by document type)
        context, doc_type = self.retrieve_context(user_question)
        
        if verbose:
            print(f"\n[DEBUG] Question: {user_question}")
            print(f"[DEBUG] Classified as: {doc_type}")
            print(f"[DEBUG] Retrieved {len(context)} context chunks")
            for i, chunk in enumerate(context[:3], 1):
                print(f"[DEBUG] Chunk {i} (first 200 chars): {chunk[:200]}...")
        
        # Generate response
        response = self.generate_response(user_question, context, doc_type)
        
        if verbose:
            print(f"[DEBUG] Generated response: {response[:200]}...")
        
        return response


# Global RAG instance
rag_system = RAGSystem()

