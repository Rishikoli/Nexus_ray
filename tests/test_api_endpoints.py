"""
Test all Nexus Ray API endpoints.
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, desc=""):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {desc}")
    print(f"{method} {path}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            print(f"✅ SUCCESS")
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:300]}...")
                return result
            except:
                print(f"Response: {response.text[:200]}")
                return response.text
        else:
            print(f"❌ FAILED")
            print(f"Error: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION FAILED - Is server running?")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


def main():
    print("\n🚀 Nexus Ray API Endpoint Tests")
    print("="*60)
    
    # Test root endpoints
    test_endpoint("GET", "/", desc="Root endpoint")
    test_endpoint("GET", "/health", desc="Health check")
    
    # Test Workflows
    print("\n\n📊 WORKFLOW ENDPOINTS")
    print("="*60)
    
    # Create workflow
    workflow_data = {
        "name": "test_workflow",
        "description": "Test workflow",
        "tasks": [
            {"id": "task1", "type": "llm", "prompt": "Hello"},
            {"id": "task2", "type": "tool", "tool_name": "processor"}
        ]
    }
    workflow = test_endpoint("POST", "/api/workflows", workflow_data, "Create workflow")
    
    # List workflows
    test_endpoint("GET", "/api/workflows", desc="List workflows")
    
    # Get specific workflow
    if workflow:
        workflow_id = workflow.get("id")
        test_endpoint("GET", f"/api/workflows/{workflow_id}", desc="Get workflow by ID")
        
        # Execute workflow
        execute_data = {"inputs": {"test": "data"}}
        execution = test_endpoint("POST", f"/api/workflows/{workflow_id}/execute", 
                                 execute_data, "Execute workflow")
        
        # Get execution status
        if execution:
            execution_id = execution.get("execution_id")
            test_endpoint("GET", f"/api/workflows/{workflow_id}/executions/{execution_id}",
                         desc="Get execution status")
    
    # Test Agents
    print("\n\n🤖 AGENT ENDPOINTS")
    print("="*60)
    
    # Register agent
    agent_data = {
        "agent_id": "test_agent_1",
        "name": "Test Agent",
        "capabilities": ["llm_analysis", "data_processing"],
        "metadata": {"version": "1.0"}
    }
    agent = test_endpoint("POST", "/api/agents/register", agent_data, "Register agent")
    
    # List agents
    test_endpoint("GET", "/api/agents", desc="List all agents")
    
    # Get specific agent
    if agent:
        agent_id = agent.get("agent_id")
        test_endpoint("GET", f"/api/agents/{agent_id}", desc="Get agent by ID")
    
    # Test LLM
    print("\n\n🧠 LLM ENDPOINTS")
    print("="*60)
    
    # List models
    test_endpoint("GET", "/api/llm/models", desc="List available models")
    
    # Generate text (this will be slow on CPU)
    print("\n⚠️  Note: LLM generation may take 10-30 seconds on CPU...")
    llm_data = {
        "prompt": "Say hello in one word",
        "max_tokens": 10,
        "temperature": 0.7
    }
    test_endpoint("POST", "/api/llm/generate", llm_data, "Generate text with LLM")
    
    # Get LLM metrics
    test_endpoint("GET", "/api/llm/metrics", desc="Get LLM metrics")
    
    # Test Metrics
    print("\n\n📈 METRICS ENDPOINTS")
    print("="*60)
    
    test_endpoint("GET", "/api/metrics", desc="Get system metrics")
    test_endpoint("GET", "/api/metrics/activity", desc="Get activity feed")
    test_endpoint("GET", "/api/metrics/llm", desc="Get LLM insights")
    
    # Test Collaboration
    print("\n\n🤝 COLLABORATION ENDPOINTS")
    print("="*60)
    
    test_endpoint("GET", "/api/collaboration/agents", desc="List collaboration agents")
    
    # Start consensus
    consensus_data = {
        "question": "Is this test working?",
        "options": ["yes", "no", "maybe"],
        "strategy": "majority_vote",
        "from_agent": "test_agent_1"
    }
    consensus = test_endpoint("POST", "/api/collaboration/consensus", 
                             consensus_data, "Start consensus")
    
    # Get consensus result
    if consensus:
        correlation_id = consensus.get("correlation_id")
        test_endpoint("GET", f"/api/collaboration/consensus/{correlation_id}",
                     desc="Get consensus result")
    
    # Test Guardrails
    print("\n\n🛡️  GUARDRAILS ENDPOINTS")
    print("="*60)
    
    # Filter content
    filter_data = {
        "text": "This is a test message",
        "strict_mode": False
    }
    test_endpoint("POST", "/api/guardrails/filter", filter_data, "Filter content")
    
    # Safety score
    score_data = {
        "text": "Hello world",
        "strict_mode": False
    }
    test_endpoint("POST", "/api/guardrails/score", score_data, "Get safety score")
    
    # Summary
    print("\n\n" + "="*60)
    print("✅ API ENDPOINT TESTING COMPLETE")
    print("="*60)
    print("\nSwagger Docs available at: http://localhost:8000/docs")
    print("ReDoc available at: http://localhost:8000/redoc")
    print()


if __name__ == "__main__":
    main()
