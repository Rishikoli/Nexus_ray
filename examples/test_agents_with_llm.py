#!/usr/bin/env python3
"""
Direct test of reference agents with REAL LLM - minimal dependencies
"""

import sys
sys.path.insert(0, '/home/aditya/Nexus-ray1')

# Test just the DrugabilityScorer directly
from src.agents.protein_drug_discovery import DrugabilityScorer
from src.agents.semiconductor_yield import RootCauseAnalyzer

print("\n🧪 Testing Reference Agents with REAL LLM\n")
print("="*70)

# Test 1: DrugabilityScorer
print("\n1️⃣  PROTEIN-DRUG DISCOVERY AGENT")
print("="*70)

scorer = DrugabilityScorer()

test_data = {
    "affinity_category": "Strong",
    "binding_energy": -11.2,
    "toxicity_score": 0.25,
    "admet_score": 0.82,
    "safety_assessment": "SAFE",
    "binding_affinity_um": 0.45
}

print("\n📊 Input Data:")
for key, val in test_data.items():
    print(f"   {key}: {val}")

print("\n🤖 Running Drug ability Analysis with REAL LLM...")
result = scorer.score(test_data)

print(f"\n✅ Results:")
print(f"   Drugability Score: {result['drugability_score']}/1.0")
print(f"   Recommendation: {result['recommendation']}")
print(f"   LLM Powered: {'✅ YES' if result['llm_powered'] else '❌ NO (fallback)'}")
print(f"   Confidence: {result['confidence']}")
print(f"\n   💬 Reasoning:")
reasoning_lines = result['reasoning'].split('\n')
for line in reasoning_lines:
    if line.strip():
        print(f"      {line.strip()}")

# Test 2: RootCauseAnalyzer
print("\n\n2️⃣  SEMICONDUCTOR YIELD OPTIMIZATION AGENT")
print("="*70)

analyzer = RootCauseAnalyzer()

test_data2 = {
    "dominant_defect_type": "particle",
    "process_stability": 0.62,
    "spatial_clusters": 4,
    "drift_detected": True,
    "defect_distribution": {"particle": 18, "scratch": 5, "void": 2}
}

print("\n📊 Input Data:")
for key, val in test_data2.items():
    print(f"   {key}: {val}")

print("\n🤖 Running Root Cause Analysis with REAL LLM...")
result2 = analyzer.analyze(test_data2)

print(f"\n✅ Results:")
print(f"   Primary Cause: {result2['primary_cause']}")
print(f"   Confidence: {result2['confidence']}")
print(f"   LLM Powered: {'✅ YES' if result2['llm_powered'] else '❌ NO (fallback)'}")
print(f"\n   🔍 Top Root Causes:")
for cause, conf in result2['root_causes'][:3]:
    print(f"      • {cause}: {conf:.2f}")
print(f"\n   💬 Reasoning:")
reasoning_lines2 = result2['reasoning'].split('\n')
for line in reasoning_lines2:
    if line.strip():
        print(f"      {line.strip()}")

print("\n\n" + "="*70)
print("🎉 REFERENCE AGENTS TEST COMPLETE!")
print("="*70)
print(f"\n✅ Protein-Drug Agent: {'Real LLM' if result['llm_powered'] else 'Fallback'}")
print(f"✅ Semiconductor Agent: {'Real LLM' if result2['llm_powered'] else 'Fallback'}")
print("\n")
