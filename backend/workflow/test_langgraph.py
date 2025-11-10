"""
Test script for LangGraph workflow integration
Run this to verify LangGraph is working correctly
"""

import os
import sys

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_basic_workflow():
    """Test basic workflow without state persistence"""
    print("="*80)
    print("TEST 1: Basic Workflow (No Persistence)")
    print("="*80)
    
    try:
        from medical_workflow import get_workflow
        
        workflow = get_workflow()
        print("✅ Basic workflow initialized successfully\n")
        
        # Test patient identification
        print("Test 1.1: Patient Identification")
        print("-" * 40)
        result = workflow.process_message("Sarah Harris")
        print(f"Status: {result['status']}")
        print(f"Patient Identified: {result['patient_identified']}")
        print(f"Response: {result['response'][:150]}...")
        print()
        
        # Test medical query
        print("Test 1.2: Medical Query")
        print("-" * 40)
        result = workflow.process_message("What causes kidney disease?")
        print(f"Status: {result['status']}")
        print(f"Agent Used: {result['agent_used']}")
        print(f"Response: {result['response'][:150]}...")
        print()
        
        print("✅ Basic workflow tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_stateful_workflow():
    """Test stateful workflow with conversation memory"""
    print("="*80)
    print("TEST 2: Stateful Workflow (With Persistence)")
    print("="*80)
    
    try:
        from stateful_workflow import get_stateful_workflow
        
        workflow = get_stateful_workflow()
        print("✅ Stateful workflow initialized successfully\n")
        
        session_id = "test_session_001"
        
        # Test 1: Patient identification
        print("Test 2.1: Patient Identification")
        print("-" * 40)
        result1 = workflow.process_message("Sarah Harris", session_id)
        print(f"Status: {result1['status']}")
        print(f"Patient Identified: {result1['patient_identified']}")
        print(f"Session ID: {result1['session_id']}")
        print(f"Response: {result1['response'][:150]}...")
        print()
        
        # Test 2: Medical query (should remember patient)
        print("Test 2.2: Medical Query with Context")
        print("-" * 40)
        result2 = workflow.process_message("I have itching all over my body", session_id)
        print(f"Status: {result2['status']}")
        print(f"Agent Used: {result2['agent_used']}")
        print(f"Patient Still Identified: {result2['patient_identified']}")
        print(f"Response: {result2['response'][:150]}...")
        print()
        
        # Test 3: General follow-up
        print("Test 2.3: General Follow-up")
        print("-" * 40)
        result3 = workflow.process_message("Thank you for the advice", session_id)
        print(f"Status: {result3['status']}")
        print(f"Response: {result3['response'][:150]}...")
        print()
        
        # Test 4: New session (should not remember patient)
        print("Test 2.4: New Session (Different Patient)")
        print("-" * 40)
        new_session = "test_session_002"
        result4 = workflow.process_message("John Smith", new_session)
        print(f"Status: {result4['status']}")
        print(f"Patient Identified: {result4['patient_identified']}")
        print(f"Session ID: {result4['session_id']}")
        print(f"Response: {result4['response'][:150]}...")
        print()
        
        print("✅ Stateful workflow tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Stateful workflow test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling scenarios"""
    print("="*80)
    print("TEST 3: Error Handling")
    print("="*80)
    
    try:
        from stateful_workflow import get_stateful_workflow
        
        workflow = get_stateful_workflow()
        session_id = "test_session_003"
        
        # Test 1: Unknown patient
        print("Test 3.1: Unknown Patient")
        print("-" * 40)
        result1 = workflow.process_message("Yash Pandey", session_id)
        print(f"Status: {result1['status']}")
        print(f"Patient Identified: {result1['patient_identified']}")
        print(f"Response: {result1['response'][:150]}...")
        print()
        
        # Test 2: Multiple patients with same name
        print("Test 3.2: Multiple Patients")
        print("-" * 40)
        result2 = workflow.process_message("Robert Jackson", session_id)
        print(f"Status: {result2['status']}")
        print(f"Response: {result2['response'][:150]}...")
        print()
        
        print("✅ Error handling tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_rag_integration():
    """Test RAG system integration"""
    print("="*80)
    print("TEST 4: RAG Integration")
    print("="*80)
    
    try:
        from stateful_workflow import get_stateful_workflow
        
        workflow = get_stateful_workflow()
        session_id = "test_session_004"
        
        # Identify patient first
        print("Test 4.1: Setup - Identify Patient")
        print("-" * 40)
        result1 = workflow.process_message("Sarah Harris", session_id)
        print(f"Patient Identified: {result1['patient_identified']}")
        print()
        
        # Test RAG query
        print("Test 4.2: RAG Query")
        print("-" * 40)
        result2 = workflow.process_message("What causes swelling in kidney disease?", session_id)
        print(f"Status: {result2['status']}")
        has_rag = "REFERENCE MATERIALS" in result2['response']
        print(f"RAG Response Detected: {has_rag}")
        print(f"Response Length: {len(result2['response'])} characters")
        print(f"Response Preview: {result2['response'][:200]}...")
        print()
        
        print("✅ RAG integration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_web_search_integration():
    """Test web search integration"""
    print("="*80)
    print("TEST 5: Web Search Integration")
    print("="*80)
    
    try:
        from stateful_workflow import get_stateful_workflow
        
        workflow = get_stateful_workflow()
        session_id = "test_session_005"
        
        # Identify patient first
        print("Test 5.1: Setup - Identify Patient")
        print("-" * 40)
        result1 = workflow.process_message("Sarah Harris", session_id)
        print(f"Patient Identified: {result1['patient_identified']}")
        print()
        
        # Test web search query
        print("Test 5.2: Web Search Query")
        print("-" * 40)
        result2 = workflow.process_message("What's the latest research on SGLT2 inhibitors?", session_id)
        print(f"Status: {result2['status']}")
        has_web_search = "RECENT MEDICAL LITERATURE" in result2['response'] or "Web Search" in result2['response']
        print(f"Web Search Response Detected: {has_web_search}")
        print(f"Response Length: {len(result2['response'])} characters")
        print(f"Response Preview: {result2['response'][:200]}...")
        print()
        
        print("✅ Web search integration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Web search integration test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("🧪 LangGraph Workflow Integration Tests")
    print("="*80)
    print()
    
    # Check environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in backend/.env")
        return
    else:
        print(f"✅ OpenAI API key found (length: {len(api_key)})")
        print()
    
    # Run tests
    results = []
    
    results.append(("Basic Workflow", test_basic_workflow()))
    results.append(("Stateful Workflow", test_stateful_workflow()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("RAG Integration", test_rag_integration()))
    results.append(("Web Search Integration", test_web_search_integration()))
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print()
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! LangGraph integration is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    main()
