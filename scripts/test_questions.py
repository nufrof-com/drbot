#!/usr/bin/env python3
"""
Test script to debug RAG responses.
Run questions and see detailed output about what's being retrieved.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.rag import rag_system
from app.config import settings


def test_question(question: str):
    """Test a single question and show detailed output."""
    print("\n" + "="*80)
    print(f"QUESTION: {question}")
    print("="*80)
    
    # Classify
    doc_type = rag_system._classify_question(question)
    print(f"\n📋 Classified as: {doc_type}")
    
    # Retrieve context
    context, retrieved_type = rag_system.retrieve_context(question)
    print(f"📚 Retrieved {len(context)} context chunks (type: {retrieved_type})")
    
    # Show context
    for i, chunk in enumerate(context, 1):
        print(f"\n--- Context Chunk {i} ({len(chunk)} chars) ---")
        print(chunk[:500] + ("..." if len(chunk) > 500 else ""))
    
    # Generate response
    print(f"\n🤖 Generating response...")
    answer = rag_system.query(question, verbose=False)
    
    print(f"\n✅ ANSWER:")
    print("-" * 80)
    print(answer)
    print("-" * 80)


def main():
    """Main function."""
    print("🧪 PartyBot RAG Debug Tool")
    print("="*80)
    
    # Initialize RAG system
    print("\n⏳ Initializing RAG system...")
    rag_system.initialize()
    print("✅ RAG system ready!\n")
    
    # Test questions from command line or use defaults
    if len(sys.argv) > 1:
        questions = [" ".join(sys.argv[1:])]
    else:
        # Default test questions
        questions = [
            "Would the party lower minimum wage?",
            "What is the party's position on healthcare?",
            "Tell me about the history of the party",
            "How does the platform differ from the historical platform?",
        ]
        print("Using default test questions. Provide a question as argument to test it.")
        print("Example: poetry run python scripts/test_questions.py 'Your question here'\n")
    
    for question in questions:
        try:
            test_question(question)
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ Testing complete!")


if __name__ == "__main__":
    main()

