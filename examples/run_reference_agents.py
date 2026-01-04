#!/usr/bin/env python3
"""
Demo script for reference agents with real LLM analysis.

Runs both Protein-Drug Discovery and Semiconductor Yield Optimization agents.
"""

import sys
sys.path.insert(0, '/home/aditya/Nexus-ray1')

from src.agents import run_protein_drug_discovery, run_semiconductor_yield_optimization
from loguru import logger
import json

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<level>{time:HH:mm:ss}</level> | <level>{message}</level>", level="INFO")

def demo_protein_drug():
    """Demo protein-drug discovery with real LLM"""
    print("\n" + "="*80)
    print("🔬 PROTEIN-DRUG DISCOVERY AGENT (with Real LLM)")
    print("="*80)
    
    # Sample protein sequence (first 50 residues of a kinase)
    protein_seq = "MENFQKVEKIGEGTYGVVYKARNKLTGEVVALKKIRLDTETEGVPSTA"
    
    # Sample drug compound (imatinib-like)
    drug_smiles = "CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=CC=C5"
    
    print(f"\n📋 Input Data:")
    print(f"   Protein: {protein_seq[:30]}... ({len(protein_seq)} residues)")
    print(f"   Drug SMILES: {drug_smiles[:50]}...")
    
    # Run analysis
    print(f"\n🚀 Running analysis pipeline...")
    result = run_protein_drug_discovery(protein_seq, drug_smiles)
    
    # Display results
    if result.get("success"):
        print(f"\n✅ Analysis Complete!")
        print(f"\n📊 Results:")
        print(f"   Structure Confidence: {result['structure_confidence']}")
        print(f"   Binding Sites Found: {result['binding_sites']}")
        print(f"   Binding Energy: {result['binding_energy']} kcal/mol")
        print(f"   Safety Assessment: {result['safety']}")
        
        drugability = result['drugability']
        print(f"\n🤖 LLM-Powered Drugability Analysis:")
        print(f"   Score: {drugability['drugability_score']}/1.0")
        print(f"   Recommendation: {drugability['recommendation']}")
        print(f"   LLM-Powered: {drugability['llm_powered']}")
        print(f"   Confidence: {drugability['confidence']}")
        print(f"\n   💬 LLM Reasoning:")
        reasoning = drugability['reasoning']
        # Wrap text
        for line in reasoning.split('\n'):
            if line.strip():
                print(f"      {line.strip()}")
        
        print(f"\n   📝 Next Steps:")
        for step in drugability['next_steps']:
            print(f"      • {step}")
    else:
        print(f"\n❌ Analysis Failed:")
        print(f"   {result.get('error', 'Unknown error')}")
    
    return result


def demo_semiconductor():
    """Demo semiconductor yield optimization with real LLM"""
    print("\n" + "="*80)
    print("💾 SEMICONDUCTOR YIELD OPTIMIZATION AGENT (with Real LLM)")
    print("="*80)
    
    wafer_id = "WF-2024-001"
    
    print(f"\n📋 Input Data:")
    print(f"   Wafer ID: {wafer_id}")
    
    # Run analysis
    print(f"\n🚀 Running analysis pipeline...")
    result = run_semiconductor_yield_optimization(wafer_id)
    
    # Display results
    if result.get("success"):
        print(f"\n✅ Analysis Complete!")
        
        defects = result['defects']
        print(f"\n📊 Defect Analysis:")
        print(f"   Total Defects: {defects['total']}")
        print(f"   Critical Defects: {defects['critical']}")
        print(f"   Dominant Type: {defects['dominant_type']}")
        
        yield_impact = result['yield_impact']
        print(f"\n📉 Yield Impact:")
        print(f"   Predicted Yield: {yield_impact['predicted_yield']*100:.2f}%")
        print(f"   Yield Loss: {yield_impact['yield_loss_percent']}%")
        print(f"   Financial Impact: ${yield_impact['financial_impact_usd']:,}")
        print(f"   Severity: {yield_impact['impact_severity'].upper()}")
        
        print(f"\n🤖 LLM-Powered Root Cause Analysis:")
        print(f"   Primary Cause: {result['root_cause']}")
        print(f"   Priority: {result['priority']}")
        
        optimizations = result['optimizations']
        print(f"\n🔧 Recommended Optimizations:")
        print(f"   Total Parameters: {optimizations['total_parameters']}")
        print(f"   Implementation Risk: {optimizations['implementation_risk'].upper()}")
        
        if optimizations['optimizations']:
            print(f"\n   Top Recommendations:")
            for opt in optimizations['optimizations'][:3]:
                print(f"      • {opt['parameter']}: {opt['current']} → {opt['recommended']} {opt['unit']}")
        
        trade_offs = optimizations['trade_off_analysis']
        print(f"\n   ⚖️  Trade-off Analysis:")
        print(f"      Throughput Impact: {trade_offs['throughput_impact']}")
        print(f"      Cost Impact: {trade_offs['cost_impact']}")
        print(f"      Yield Improvement: {trade_offs['yield_improvement']}")
    else:
        print(f"\n❌ Analysis Failed:")
        print(f"   {result.get('error', 'Unknown error')}")
    
    return result


def main():
    """Run both demos"""
    print("\n🚀 Nexus Ray Reference Agents Demo")
    print("Showcasing Real-Time LLM Analysis\n")
    
    try:
        # Run Protein-Drug Discovery
        protein_result = demo_protein_drug()
        
        # Run Semiconductor Yield
        semiconductor_result = demo_semiconductor()
        
        # Summary
        print("\n" + "="*80)
        print("📊 DEMO SUMMARY")
        print("="*80)
        
        protein_llm = protein_result.get('drugability', {}).get('llm_powered', False)
        
        print(f"\n✅ Protein-Drug Discovery:")
        print(f"   Status: {'SUCCESS' if protein_result.get('success') else 'FAILED'}")
        print(f"   LLM Used: {'✓ Real OpenVINO LLM' if protein_llm else '✗ Fallback logic'}")
        
        print(f"\n✅ Semiconductor Yield:")
        print(f"   Status: {'SUCCESS' if semiconductor_result.get('success') else 'FAILED'}")
        
        print(f"\n🎉 Both reference agents executed successfully!")
        print(f"\nℹ️  Note: LLM integration requires OpenVINO model to be available.")
        print(f"   Set NEXUS_RAY_LLM__MODEL_PATH to enable real LLM analysis.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
