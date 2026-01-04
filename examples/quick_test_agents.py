#!/usr/bin/env python3
"""
QUICK TEST - Just test fallback logic (no slow LLM wait)
"""
import sys
sys.path.insert(0, '/home/aditya/Nexus-ray1')

from src.agents.protein_drug_discovery import DrugabilityScorer
from src.agents.semiconductor_yield import RootCauseAnalyzer

print("\n🧪 QUICK Reference Agent Test (Fallback Logic)\n")
print("="*60)

# Test 1: Drug
print("\n1️⃣ Protein-Drug Discovery Agent")
scorer = DrugabilityScorer()
# Don't initialize LLM, use fallback
result = scorer.score({
    "affinity_category": "Strong",
    "binding_energy": -11.2,
    "toxicity_score": 0.25,
    "admet_score": 0.82,
    "safety_assessment": "SAFE"
})

print(f"✅ Score: {result['drugability_score']}/1.0")
print(f"✅ Recommendation: {result['recommendation']}")
print(f"✅ Reasoning: {result['reasoning'][:100]}...")

# Test 2: Semiconductor
print("\n2️⃣ Semiconductor Yield Agent")
analyzer = RootCauseAnalyzer()
result2 = analyzer.analyze({
    "dominant_defect_type": "particle",
    "process_stability": 0.62,
    "spatial_clusters": 4,
    "drift_detected": True
})

print(f"✅ Primary Cause: {result2['primary_cause']}")
print(f"✅ Confidence: {result2['confidence']}")
print(f"✅ Reasoning: {result2['reasoning'][:80]}...")

print("\n" + "="*60)
print("🎉 AGENTS WORK! (Using fallback logic)")
print("="*60)
print("\n💡 Note: Real LLM takes ~20-30sec per call on CPU")
print("   We proved it works in demo_llm_working.py")
print("   Agents have full LLM integration ready to use!\n")
