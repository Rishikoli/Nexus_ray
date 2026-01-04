import time
import json
import psutil
import numpy as np
from pathlib import Path
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer
import concurrent.futures

# Configuration
MODELS = {
    "mistral-7b-int8": Path("d:/Intelfinal/Nexus_ray/models/mistral-7b-int8"),
    "mistral-7b-fp16": Path("d:/Intelfinal/Nexus_ray/models/mistral-7b-fp16")
}
CONCURRENCY_LEVELS = [1, 2] # Reduced for stability on CPU
PROMPTS = [
    "Safety check: Axis Y vibration 12mm/s. Immediate action?",
    "Boiler 4: Pressure 14 bar. Status report."
]

RESULTS_FILE = "d:/Intelfinal/Nexus_ray/industrial_stress_test_results.json"

def agent_worker(model, tokenizer, prompt_idx):
    try:
        prompt = PROMPTS[prompt_idx % len(PROMPTS)]
        inputs = tokenizer(prompt, return_tensors="pt")
        
        start = time.time()
        # Very short generation for stress test speed
        outputs = model.generate(**inputs, max_new_tokens=15)
        duration = time.time() - start
        
        tokens = outputs.shape[1] - inputs.input_ids.shape[1]
        return {
            "duration": duration,
            "tps": tokens / duration if duration > 0 else 0,
            "tokens": tokens
        }
    except Exception as e:
        print(f"      ❌ Worker Error: {e}")
        return None

def run_stress_test():
    print("🏁 Industrial Stress Test Starting...")
    
    final_results = {}

    for model_name, model_path in MODELS.items():
        print(f"\n📦 Evaluating Model: {model_name}")
        if not model_path.exists():
            print(f"   ⚠️ Skip: {model_path} not found.")
            continue

        print(f"   📥 Loading {model_name}... (Step 1/2: RAM Load)")
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            print(f"   ⚙️ Compiling OpenVINO Graph... (Step 2/2: Optimization)")
            print(f"      [!] This can take 2-4 minutes on first run. Please do not interrupt.")
            model = OVModelForCausalLM.from_pretrained(model_path, device="CPU")
            print(f"   ✅ {model_name} Ready for Stress Test.")
        except Exception as e:
            print(f"   ❌ Load Failed: {e}")
            continue

        model_results = {}

        for level in CONCURRENCY_LEVELS:
            print(f"   🔥 Testing Concurrency: {level} Agents")
            latencies = []
            tps_values = []
            
            # Measure CPU load as a proxy for thermal effort
            cpu_before = psutil.cpu_percent(interval=None)
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=level) as executor:
                futures = [executor.submit(agent_worker, model, tokenizer, i) for i in range(level * 2)]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res:
                        latencies.append(res["duration"])
                        tps_values.append(res["tps"])
            
            end_time = time.time()
            cpu_after = psutil.cpu_percent(interval=None)
            
            if not latencies:
                continue

            # Metrics
            p50 = np.percentile(latencies, 50)
            p99 = np.percentile(latencies, 99)
            avg_tps = np.mean(tps_values)
            
            model_results[str(level)] = {
                "p50_latency": round(p50, 2),
                "p99_latency": round(p99, 2),
                "avg_tps": round(avg_tps, 2),
                "cpu_load_proxy": round((cpu_before + cpu_after) / 2, 1)
            }
            print(f"      [L{level}] P99: {model_results[str(level)]['p99_latency']}s | TPS: {model_results[str(level)]['avg_tps']}")

        final_results[model_name] = model_results
        
        # Cleanup to allow next model to load
        del model
        del tokenizer
        time.sleep(2)

    # Save
    with open(RESULTS_FILE, "w") as f:
        json.dump(final_results, f, indent=2)
    print(f"\n💾 Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_stress_test()
