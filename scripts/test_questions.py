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
        test_results = []
    else:
        # Default test questions covering various scenarios
        test_cases = [
            # (question, expected_type, description)
            ("Would the party lower minimum wage?", "platform", "Negative question - should state party supports raising it"),
            ("Would the party decrease minimum wage?", "platform", "Negative question - should state party supports raising it"),
            ("Does the party oppose universal healthcare?", "platform", "Negative question - should state party supports it"),
            
            # General platform questions
            ("What is the party's position on healthcare?", "platform", "General platform question"),
            ("Tell me about the party", "platform", "General question - should default to platform"),
            ("What are the party's views on climate change?", "platform", "Platform policy question"),
            
            # History/origin questions (should use Wikipedia document)
            ("Where did the party come from?", "history", "Origin question - should use history docs"),
            ("Where was the party founded?", "history", "Location question - should provide location, not just dates"),
            ("Tell me about the history of the party", "history", "History question"),
            ("When was the party founded?", "history", "Founding date question"),
            ("Who founded the Democratic-Republican Party?", "history", "Founder question"),
            ("Now when, where", "history", "Follow-up asking for both time and location"),
            
            # Comparative questions (should use both documents)
            ("How does the platform differ from the historical platform?", "both", "Comparative question - needs both docs"),
            ("Compare the historical and modern party positions", "both", "Comparison question"),
            ("What changed between the historical party and today?", "both", "Change question"),
            ("What has changed since the original party was revived?", "both", "Revival question - should compare historical vs modern"),
        ]
        
        questions = [q[0] for q in test_cases]
        test_results = test_cases
        
        print("Using default test questions covering:")
        print("  - Negative questions (lower/decrease/oppose)")
        print("  - General platform questions")
        print("  - History/origin questions")
        print("  - Comparative questions")
        print("\nProvide a question as argument to test it.")
        print("Example: poetry run python scripts/test_questions.py 'Your question here'\n")
    
    results_summary = []
    
    for i, question in enumerate(questions):
        try:
            # Get expected type if we have test cases
            expected_type = None
            description = None
            if test_results:
                expected_type = test_results[i][1]
                description = test_results[i][2]
            
            test_question(question)
            
            # Check classification if we have expected type
            if expected_type:
                actual_type = rag_system._classify_question(question)
                status = "✅" if actual_type == expected_type else "❌"
                results_summary.append({
                    "question": question,
                    "expected": expected_type,
                    "actual": actual_type,
                    "status": status,
                    "description": description
                })
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            if test_results:
                results_summary.append({
                    "question": question,
                    "expected": test_results[i][1] if i < len(test_results) else "unknown",
                    "actual": "ERROR",
                    "status": "❌",
                    "description": test_results[i][2] if i < len(test_results) else ""
                })
    
    # Print summary if we ran test cases
    if results_summary:
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        for result in results_summary:
            print(f"\n{result['status']} {result['question']}")
            print(f"   Expected: {result['expected']}, Got: {result['actual']}")
            if result['description']:
                print(f"   {result['description']}")
        
        passed = sum(1 for r in results_summary if r['status'] == "✅")
        total = len(results_summary)
        print(f"\n📈 Results: {passed}/{total} classifications correct")
    
    print("\n" + "="*80)
    print("✅ Testing complete!")


if __name__ == "__main__":
    main()

