#!/bin/bash
# Nexus Ray API Test Suite - curl commands

API_URL="http://localhost:8000"

echo "🚀 Nexus Ray API Test Suite"
echo "="*60
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
curl -s $API_URL/health | jq
echo ""

# Test 2: Root Endpoint
echo -e "${BLUE}Test 2: Root Endpoint${NC}"
curl -s $API_URL/ | jq
echo ""

# Test 3: Create Workflow
echo -e "${BLUE}Test 3: Create Workflow${NC}"
curl -s -X POST $API_URL/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_workflow",
    "description": "Test workflow",
    "tasks": [
      {"id": "task1", "type": "llm", "prompt": "Hello"},
      {"id": "task2", "type": "tool", "tool_name": "processor"}
    ]
  }' | jq
echo ""

# Test 4: List Workflows
echo -e "${BLUE}Test 4: List Workflows${NC}"
curl -s $API_URL/api/workflows | jq
echo ""

# Test 5: Register Agent
echo -e "${BLUE}Test 5: Register Agent${NC}"
curl -s -X POST $API_URL/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent_1",
    "name": "Test Agent",
    "capabilities": ["llm_analysis", "data_processing"],
    "metadata": {"version": "1.0"}
  }' | jq
echo ""

# Test 6: List Agents
echo -e "${BLUE}Test 6: List Agents${NC}"
curl -s $API_URL/api/agents | jq
echo ""

# Test 7: List LLM Models
echo -e "${BLUE}Test 7: List LLM Models${NC}"
curl -s $API_URL/api/llm/models | jq
echo ""

# Test 8: Get System Metrics
echo -e "${BLUE}Test 8: System Metrics${NC}"
curl -s $API_URL/api/metrics | jq
echo ""

# Test 9: Get LLM Metrics
echo -e "${BLUE}Test 9: LLM Metrics${NC}"
curl -s $API_URL/api/llm/metrics | jq
echo ""

# Test 10: Filter Content (Guardrails)
echo -e "${BLUE}Test 10: Content Filter${NC}"
curl -s -X POST $API_URL/api/guardrails/filter \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a clean test message",
    "strict_mode": false
  }' | jq
echo ""

# Test 11: Safety Score
echo -e "${BLUE}Test 11: Safety Score${NC}"
curl -s -X POST $API_URL/api/guardrails/score \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "strict_mode": false
  }' | jq
echo ""

# Test 12: Start Consensus
echo -e "${BLUE}Test 12: Start Consensus${NC}"
curl -s -X POST $API_URL/api/collaboration/consensus \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Is this a good idea?",
    "options": ["yes", "no", "maybe"],
    "strategy": "majority_vote",
    "from_agent": "test_agent_1"
  }' | jq
echo ""

# Test 13: Protein-Drug Discovery
echo -e "${BLUE}Test 13: Protein-Drug Discovery${NC}"
curl -s -X POST $API_URL/api/reference/protein-drug \
  -H "Content-Type: application/json" \
  -d '{
    "protein_sequence": "MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIR",
    "drug_smiles": "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=CC=C5"
  }' | jq
echo ""

# Test 14: Semiconductor Yield
echo -e "${BLUE}Test 14: Semiconductor Yield Optimization${NC}"
curl -s -X POST $API_URL/api/reference/semiconductor \
  -H "Content-Type: application/json" \
  -d '{
    "wafer_id": "W123456",
    "defect_data": {
      "total": 150,
      "particle": 50,
      "scratch": 40,
      "pattern": 35,
      "other": 25
    }
  }' | jq
echo ""

# Test 15: Get Protein-Drug Info
echo -e "${BLUE}Test 15: Protein-Drug Agent Info${NC}"
curl -s $API_URL/api/reference/protein-drug/info | jq
echo ""

# Test 16: Get Semiconductor Info
echo -e "${BLUE}Test 16: Semiconductor Agent Info${NC}"
curl -s $API_URL/api/reference/semiconductor/info | jq
echo ""

# Test 17: LLM Generation (Warning: Slow on CPU!)
echo -e "${BLUE}Test 17: LLM Text Generation (may take 10-30s)${NC}"
curl -s -X POST $API_URL/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Say hello in one sentence",
    "max_tokens": 10,
    "temperature": 0.7
  }' | jq
echo ""

echo -e "${GREEN}✅ All API tests complete!${NC}"
echo ""
echo "📊 API Documentation: $API_URL/docs"
echo "📖 ReDoc: $API_URL/redoc"
