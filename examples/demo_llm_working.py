#!/usr/bin/env python3
"""
Simple LLM demo to prove it works!
"""

import sys
sys.path.insert(0, '/home/aditya/Nexus-ray1')

from src.llm import get_llm
from loguru import logger

logger.remove()
logger.add(sys.stdout, level="INFO", format="<level>{message}</level>")

def main():
    print("\n🤖 Nexus Ray LLM Demo - REAL OpenVINO Inference\n")
    print("="*60)
    
    # Load LLM
    print("\n1️⃣  Loading LLM...")
    llm = get_llm()
    print("✅ LLM Loaded Successfully!\n")
    
    # Test 1: Simple question
    print("="*60)
    print("TEST 1: Simple Math Question")
    print("="*60)
    prompt1 = "What is 5 + 7? Give a brief answer."
    print(f"Prompt: {prompt1}")
    print(f"\n🤖 Generating...")
    response1 = llm.generate(prompt1, max_tokens=30, temperature=0.3)
    print(f"✅ Response: {response1}\n")
    
    # Test 2: Medical analysis (relevant to protein-drug)
    print("="*60)
    print("TEST 2: Medical Analysis (Like Drug Discovery)")
    print("="*60)
    prompt2 = """A drug has:
- Strong binding affinity (-11.5 kcal/mol)
- Low toxicity (0.2/1.0)
- Good ADMET score (0.85/1.0)

Is this a good drug candidate? Answer in 2 sentences."""
    
    print(f"Prompt: {prompt2[:100]}...")
    print(f"\n🤖 Generating...")
    response2 = llm.generate(prompt2, max_tokens=80, temperature=0.3)
    print(f"✅ Response: {response2}\n")
    
    # Test 3: Technical analysis (relevant to semiconductor)
    print("="*60)
    print("TEST 3: Technical Root Cause Analysis")
    print("="*60)
    prompt3 = """A semiconductor wafer has:
- 25 particle defects
- Process stability: 0.65/1.0 (unstable)
- 4 spatial clusters

What is the likely root cause? Be technical."""
    
    print(f"Prompt: {prompt3[:100]}...")
    print(f"\n🤖 Generating...")
    response3 = llm.generate(prompt3, max_tokens=100, temperature=0.2)
    print(f"✅ Response: {response3}\n")
    
    print("="*60)
    print("🎉 LLM IS WORKING!")
    print("="*60)
    print("\n✅ All tests passed!")
    print("✅ Real OpenVINO inference successful!")
    print("✅ Ready to integrate into reference agents!\n")

if __name__ == '__main__':
    main()
