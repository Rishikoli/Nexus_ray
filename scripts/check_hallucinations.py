import time
import json
from pathlib import Path
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer
import torch

print("🏁 Quality Check Script Started...")

# Configuration
ROOT = Path("d:/Intelfinal/Nexus_ray")
MODELS = {
    "Baseline (FP16)": ROOT / "models/mistral-7b-fp16",
    "Optimized (INT8)": ROOT / "models/mistral-7b-int8"
}

# Critical Safety Prompts
SAFETY_PROMPTS = [
    {
        "id": "chemical_spill",
        "prompt": "Line A2 reports a Sulfuric Acid leak (approx 20L). Proximity sensors show 3 workers nearby. Draft urgent response instructions.",
        "must_include": ["ppe", "containment", "neutralize", "evacuate"]
    },
    {
        "id": "robotic_anomaly",
        "prompt": "Pick-and-place robot R-82 deviates from path by 15cm while workers are inside the zone. Light curtain failed. Action required.",
        "must_include": ["e-stop", "interlock", "isolation"]
    }
]

RESULTS_FILE = "d:/Intelfinal/Nexus_ray/quality_comparison_report.json"

def get_response(model_path, prompt):
    print(f"   Loading {model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = OVModelForCausalLM.from_pretrained(model_path, device="CPU")
        
        inputs = tokenizer(prompt, return_tensors="pt")
        print(f"   Generating Response...")
        start = time.time()
        # Using a small max_new_tokens for speed during this comparison
        outputs = model.generate(**inputs, max_new_tokens=60, temperature=0.7, do_sample=True)
        duration = time.time() - start
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        # Cleanup to free memory
        del model
        del tokenizer
        if torch.cuda.is_available(): torch.cuda.empty_cache()
        
        return response.strip(), duration
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, 0

def run_quality_check():
    report = []
    
    for test in SAFETY_PROMPTS:
        print(f"\n🧪 Testing Case: {test['id']}")
        case_results = {"id": test['id'], "prompt": test['prompt'], "responses": {}}
        
        for name, path in MODELS.items():
            print(f"👉 Querying {name}...")
            response, duration = get_response(Path(path), test['prompt'])
            
            if response:
                # Basic health check: find keywords
                missing = [word for word in test['must_include'] if word.lower() not in response.lower()]
                health_score = 100 * (1 - len(missing)/len(test['must_include']))
                
                case_results["responses"][name] = {
                    "text": response,
                    "duration": round(duration, 2),
                    "health_score": round(health_score, 1),
                    "missing_keywords": missing
                }
        
        report.append(case_results)
    
    print(f"\n💾 Saving report to {RESULTS_FILE}")
    with open(RESULTS_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print("✅ Quality Check Complete!")

if __name__ == "__main__":
    run_quality_check()
