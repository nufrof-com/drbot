"""Retrieval-Augmented Generation (RAG) functionality for Democratic Republican SpokesBot."""
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
        
        # Load documents from DRP Platform v3.0 directory
        documents = self._load_documents()
        
        if not documents:
            print("Warning: No documents found in platform directory")
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
        """Load text documents from the DRP Platform v3.0 directory with metadata."""
        documents = []
        # Resolve to absolute path
        platform_dir = os.path.abspath(settings.data_directory)
        
        if not os.path.exists(platform_dir):
            print(f"Platform directory {platform_dir} does not exist")
            return documents
        
        # Load all .txt files from platform directory (sorted for consistent ordering)
        txt_files = sorted([f for f in os.listdir(platform_dir) if f.endswith('.txt')])
        
        for filename in txt_files:
            filepath = os.path.join(platform_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        # Extract section name from filename (e.g., "01_introduction" -> "Introduction")
                        section_name = filename.replace('.txt', '').split('_', 1)[-1].replace('_', ' ').title()
                        
                        # Create Document with metadata
                        doc = Document(
                            page_content=content,
                            metadata={
                                "source": filename,
                                "section": section_name,
                                "doc_type": "platform",
                                "version": "v3.0"
                            }
                        )
                        documents.append(doc)
                        print(f"Loaded: {filename} (section: {section_name})")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        return documents
    
    def _classify_question(self, query: str) -> str:
        """
        Classify question type. Since we only have platform documents now,
        all questions are about the platform.
        
        Returns:
            "platform" (always, since we only have platform documents)
        """
        # All questions are about the platform now
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
    
    def retrieve_context(self, query: str, top_k: int = 8) -> Tuple[List[str], str]:
        """
        Retrieve relevant context chunks for a query from platform documents.
        Uses a larger top_k to provide more context for reasoning.
        
        Returns:
            Tuple of (context_chunks, doc_type)
        """
        if not self.vectorstore:
            return [], "platform"
        
        try:
            # Expand query for better retrieval
            expanded_query = self._expand_query(query)
            
            # Retrieve more chunks to enable better reasoning (increased from 5 to 8)
            results = self.vectorstore.similarity_search(
                expanded_query,
                k=top_k,
                filter={"doc_type": "platform"}
            )
            
            # Also retrieve related context by searching for key terms in the query
            # This helps find related sections that might be relevant for reasoning
            query_words = [w for w in query.lower().split() if len(w) > 3]  # Filter short words
            related_results = []
            for word in query_words[:3]:  # Try top 3 meaningful words
                try:
                    word_results = self.vectorstore.similarity_search(
                        word,
                        k=3,
                        filter={"doc_type": "platform"}
                    )
                    related_results.extend(word_results)
                except:
                    pass
            
            # Combine and deduplicate
            all_results = results + related_results
            
            # If no results with filter, try without filter as fallback
            if not all_results:
                print(f"Warning: No platform documents found, searching all documents...")
                all_results = self.vectorstore.similarity_search(expanded_query, k=top_k)
            
            # Also try original query if expanded didn't work well
            if len(all_results) < 3:
                original_results = self.vectorstore.similarity_search(
                    query,
                    k=top_k,
                    filter={"doc_type": "platform"}
                )
                all_results.extend(original_results)
            
            # Remove duplicates and return
            seen_content = set()
            unique_results = []
            for r in all_results:
                content = r.page_content.strip()
                if content not in seen_content and len(content) > 50:
                    seen_content.add(content)
                    unique_results.append(content)
            
            # Limit to top_k to avoid overwhelming the model
            return unique_results[:top_k], "platform"
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
        """Generate a response using Ollama LLM with reasoning capabilities."""
        # Construct prompt for platform questions with reasoning instructions
        context_text = "\n\n".join(context) if context else ""
        
        # Check if we have context - if not, the retrieval failed
        if not context_text or len(context_text.strip()) < 50:
            return f"I'm only able to discuss our party's official positions and policies. I couldn't find relevant information in our platform documents to answer your question. Please try rephrasing your question or ask about a different topic."
        
        # Enhanced prompt that encourages reasoning while staying grounded
        # Bot speaks in first person as a member of the party
        prompt = f"""You are a spokesperson for the {settings.party_name}. You are answering questions about our party's official platform. Use the platform information below to answer the question as if you are a member of the party speaking in first person.

Platform Information:
{context_text}

Question: {query}

Instructions:
1. Answer as a member of the {settings.party_name} speaking in first person (use "we", "our", "us", "I").
2. Base your answer on the platform information provided above. Stay true to our party's stated positions and principles.
3. If the question is directly answered in the platform, provide that answer clearly in first person.
4. If the question is not directly answered, use logical reasoning to infer an answer from our platform's principles, stated positions, and related policies.
5. When reasoning:
   - Connect related concepts from different sections of the platform
   - Apply our core principles (balanced problem solving, transparency, evidence-based policy, civility, innovation) to the question
   - Consider how our stated positions on related topics might inform this question
   - Be explicit about what you're inferring vs. what's directly stated
6. If you cannot reasonably infer an answer from the platform, say so clearly rather than speculating.
7. Provide a clear, direct answer in first person. Do not include formatting markers, labels like "Answer:", or meta-commentary. Just answer the question naturally as a party member would."""
        
        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.ollama_temperature,
                        # Add other parameters that help with reasoning
                        "top_p": 0.9,  # Nucleus sampling for more focused reasoning
                        "top_k": 40,   # Limit vocabulary for more coherent reasoning
                    }
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
        Process a user question and return a response with reasoning.
        
        Args:
            user_question: The user's question
            verbose: If True, print debug information
        
        Returns:
            The generated response
        """
        # Retrieve relevant context (with more chunks for better reasoning)
        context, doc_type = self.retrieve_context(user_question, top_k=8)
        
        if verbose:
            print(f"\n[DEBUG] Question: {user_question}")
            print(f"[DEBUG] Classified as: {doc_type}")
            print(f"[DEBUG] Retrieved {len(context)} context chunks")
            for i, chunk in enumerate(context[:3], 1):
                print(f"[DEBUG] Chunk {i} (first 200 chars): {chunk[:200]}...")
        
        # Generate response with reasoning
        response = self.generate_response(user_question, context, doc_type)
        
        if verbose:
            print(f"[DEBUG] Generated response: {response[:200]}...")
        
        return response


# Global RAG instance
rag_system = RAGSystem()

