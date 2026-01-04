import time
import json
import psutil
import torch
import numpy as np
from pathlib import Path
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer

# Configuration
# Configuration
MODELS = {
    "mistral-7b-int8": "mistral-7b-int8",
    "mistral-7b-fp16": "models/mistral-7b-fp16"
}

MODEL_DIR = Path("d:/Intelfinal/Nexus_ray") # Root dir, models are relative

# Prompts from the Notebook
PROMPTS = [
    "Quick safety check: Machine 5 is vibrating.",
    "System status: All systems nominal."
]

RESULTS_FILE = "d:/Intelfinal/Nexus_ray/benchmark_results.json"

def download_model(model_id, local_dir):
    print(f"⬇️ Downloading {model_id} to {local_dir}...")
    try:
        # Use Optimum to load/download
        model = OVModelForCausalLM.from_pretrained(model_id, export=False)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Save locally
        model.save_pretrained(local_dir)
        tokenizer.save_pretrained(local_dir)
        print(f"✅ Saved {model_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {model_id}: {e}")
        return False

def benchmark_model(model_name: str, model_path: Path):
    print(f"\n🚀 Benchmarking {model_name}...")
    
    device = "CPU"
    print(f"   Device: {device}")
    
    # Load
    start_load = time.time()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        # Force OV model for consistent measuring inside this script
        model = OVModelForCausalLM.from_pretrained(model_path, device=device)
    except Exception as e:
        print(f"   ❌ Load Failed: {e}")
        return None
        
    load_time = time.time() - start_load
    print(f"   Example Load Time: {load_time:.2f}s")
    
    # Warmup
    print("   🔥 Warming up...")
    model.generate(**tokenizer("Hello", return_tensors="pt"), max_new_tokens=5)
    
    metrics = {
        "model_name": model_name,
        "load_time_seconds": load_time,
        "latencies": [],
        "tokens_per_second": [],
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }
    
    for i, prompt in enumerate(PROMPTS):
        print(f"   🧪 Run {i+1}: {prompt[:30]}...")
        inputs = tokenizer(prompt, return_tensors="pt")
        input_tokens = inputs.input_ids.shape[1]
        
        start_gen = time.time()
        output = model.generate(**inputs, max_new_tokens=10)
        end_gen = time.time()
        
        total_time = end_gen - start_gen
        out_tokens = output.shape[1] - input_tokens
        tps = out_tokens / total_time
        
        print(f"      -> {out_tokens} tokens in {total_time:.2f}s ({tps:.2f} t/s)")
        
        metrics["latencies"].append(total_time)
        metrics["tokens_per_second"].append(tps)
        
    # Calculate averages
    avg_tps = np.mean(metrics["tokens_per_second"])
    avg_lat = np.mean(metrics["latencies"])
    print(f"   📊 Average TPS: {avg_tps:.2f}")
    
    return {
        "model": model_name,
        "avg_tokens_per_second": round(avg_tps, 2),
        "avg_latency_per_request": round(avg_lat, 2),
        "load_time": round(load_time, 2),
        "memory_mb": round(metrics["memory_usage_mb"], 2)
    }

import sys

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if a specific model was requested via CLI
    requested_model = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 1. Download/Ensure Models
    for name, hf_id in MODELS.items():
        if requested_model and name != requested_model:
            continue
            
        local_path = MODEL_DIR / name
        bin_file = local_path / "openvino_model.bin"
        
        if not local_path.exists() or not bin_file.exists() or bin_file.stat().st_size < 500 * 1024 * 1024:
            print(f"📥 {name} is missing or incomplete. Attempting recovery...")
            download_model(hf_id, local_path)
        else:
            print(f"✅ {name} already exists and looks complete.")

    # 2. Benchmark
    new_results = []
    
    # Load existing results if any
    try:
        with open(RESULTS_FILE, "r") as f:
            all_results = json.load(f)
            if not isinstance(all_results, list):
                all_results = []
    except (FileNotFoundError, json.JSONDecodeError):
        all_results = []

    for name in MODELS.keys():
        if requested_model and name != requested_model:
            continue
            
        local_path = MODEL_DIR / name
        result = benchmark_model(name, local_path)
        if result:
            # Update or append
            found = False
            for i, existing in enumerate(all_results):
                if existing["model"] == name:
                    all_results[i] = result
                    found = True
                    break
            if not found:
                all_results.append(result)
            
    # 3. Save
    print(f"\n💾 Saving results to {RESULTS_FILE}...")
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
        
    print("✅ Done!")

if __name__ == "__main__":
    main()
