import time
import json
import psutil
import torch
import numpy as np
from pathlib import Path
from optimum.intel import OVModelForCausalLM, OVModelForSequenceClassification
from transformers import AutoTokenizer

# Configuration
# Configuration
MODELS = {
    "mistral-7b-int8": "OpenVINO/mistral-7b-v0.1-int8-ov",
    "mistral-7b-fp16": "mistralai/Mistral-7B-v0.1",
    "tinyllama-int8": "OpenVINO/tinyllama-1.1b-chat-v1.0-int8-ov",
    "tinyllama-int4": "OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov",
    "tinyllama-fp16": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "bge-reranker-fp16": "BAAI/bge-reranker-large",
    "bge-reranker-ov": "BAAI/bge-reranker-large"
}

MODEL_DIR = Path("models")

# Prompts from the Notebook
PROMPTS = [
    "Quick safety check: Machine 5 is vibrating.",
    "System status: All systems nominal."
]

RESULTS_FILE = "benchmark_results.json"

def download_model(model_id, local_dir, task="causal-lm", framework="ov"):
    print(f"⬇️ Downloading {model_id} to {local_dir} (Task: {task}, Framework: {framework})...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        if framework == "pt":
            from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification
            if task == "causal-lm":
                model = AutoModelForCausalLM.from_pretrained(model_id)
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_id)
            model.save_pretrained(local_dir)
        else:
            from optimum.intel import OVModelForCausalLM, OVModelForSequenceClassification
            if task == "causal-lm":
                model = OVModelForCausalLM.from_pretrained(model_id, export=True)
            else:
                model = OVModelForSequenceClassification.from_pretrained(model_id, export=True)
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
    
    # Cold Start Measurement
    start_load = time.time()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = OVModelForCausalLM.from_pretrained(model_path, device=device)
    except Exception as e:
        print(f"   ❌ Load Failed: {e}")
        return None
        
    cold_start_time = time.time() - start_load
    print(f"   ❄️ Cold Start (Load Time): {cold_start_time:.2f}s")
    
    # Warmup
    print("   🔥 Warming up...")
    model.generate(**tokenizer("Hello", return_tensors="pt"), max_new_tokens=5)
    
    metrics = {
        "model_name": model_name,
        "cold_start_seconds": cold_start_time,
        "latencies": [],
        "ttft_list": [],
        "tokens_per_second": [],
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024
    }
    
    # Run multiple iterations for statistical significance
    ITERATIONS = 5
    for i in range(ITERATIONS):
        prompt = PROMPTS[i % len(PROMPTS)]
        print(f"   🧪 Run {i+1}/{ITERATIONS}: {prompt[:30]}...")
        inputs = tokenizer(prompt, return_tensors="pt")
        input_tokens = inputs.input_ids.shape[1]
        
        # Measure TTFT (Time To First Token)
        # Note: Optimum/Transformers streaming would be ideal, 
        # but we estimate based on a 1-token generation
        start_ttft = time.time()
        model.generate(**inputs, max_new_tokens=1)
        ttft = time.time() - start_ttft
        
        # Measure Total Generation
        start_gen = time.time()
        output = model.generate(**inputs, max_new_tokens=20)
        end_gen = time.time()
        
        total_time = end_gen - start_gen
        out_tokens = output.shape[1] - input_tokens
        tps = out_tokens / total_time
        
        metrics["latencies"].append(total_time)
        metrics["ttft_list"].append(ttft)
        metrics["tokens_per_second"].append(tps)
        
    # Statistical Calculations
    avg_tps = np.mean(metrics["tokens_per_second"])
    p50_lat = np.percentile(metrics["latencies"], 50)
    p99_lat = np.percentile(metrics["latencies"], 99)
    avg_ttft = np.mean(metrics["ttft_list"])
    
    print(f"   📊 Results for {model_name}:")
    print(f"      - TPS: {avg_tps:.2f}")
    print(f"      - TTFT: {avg_ttft*1000:.1f}ms")
    print(f"      - P50 Latency: {p50_lat:.2f}s")
    print(f"      - P99 Latency: {p99_lat:.2f}s")
    
    return {
        "model": model_name,
        "avg_tokens_per_second": round(avg_tps, 2),
        "avg_ttft_ms": round(avg_ttft * 1000, 2),
        "p50_latency": round(p50_lat, 2),
        "p99_latency": round(p99_lat, 2),
        "cold_start_time": round(cold_start_time, 2),
        "memory_mb": round(metrics["memory_usage_mb"], 2)
    }

import sys

def benchmark_reranker(model_name: str, model_path: Path, framework: str = "ov"):
    print(f"\n🚀 Benchmarking Reranker: {model_name} ({framework.upper()})...")
    
    start_load = time.time()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if framework == "ov":
            device = "CPU"
            from optimum.intel import OVModelForSequenceClassification
            model = OVModelForSequenceClassification.from_pretrained(model_path, device=device)
        else:
            device = "cpu"
            from transformers import AutoModelForSequenceClassification
            model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
    except Exception as e:
        print(f"   ❌ Load Failed: {e}")
        return None
        
    cold_start_time = time.time() - start_load
    print(f"   ❄️ Cold Start (Load Time): {cold_start_time:.2f}s")
    
    # Pairs for reranking
    pairs = [["What is the capital of France?", "Paris is the capital of France."]] * 10
    
    print("   🔥 Warming up...")
    inputs = tokenizer(pairs[0], padding=True, truncation=True, return_tensors="pt")
    model(**inputs)
    
    latencies = []
    ITERATIONS = 10
    for i in range(ITERATIONS):
        start = time.time()
        inputs = tokenizer(pairs[0], padding=True, truncation=True, return_tensors="pt")
        model(**inputs)
        latencies.append(time.time() - start)
        
    avg_latency = np.mean(latencies)
    pairs_per_sec = 1.0 / avg_latency
    
    print(f"   📊 Results for {model_name}:")
    print(f"      - Latency/Pair: {avg_latency*1000:.2f}ms")
    print(f"      - Pairs/Sec: {pairs_per_sec:.2f}")
    
    return {
        "model": model_name,
        "avg_latency_ms": round(avg_latency * 1000, 2),
        "pairs_per_second": round(pairs_per_sec, 2),
        "cold_start_time": round(cold_start_time, 2),
        "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2)
    }

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
        pytorch_file = local_path / "pytorch_model.bin"
        safetensors_file = local_path / "model.safetensors"
        
        exists = local_path.exists() and (bin_file.exists() or pytorch_file.exists() or safetensors_file.exists())
        
        if not exists:
            print(f"📥 {name} is missing or incomplete. Attempting recovery...")
            task = "sequence-classification" if "reranker" in name.lower() else "causal-lm"
            framework = "pt" if "fp16" in name.lower() or "fp32" in name.lower() else "ov"
            # Special case for mistral-ov-int8 which is already exported
            if "ov" in name.lower(): framework = "ov"
            
            download_model(hf_id, local_path, task=task, framework=framework)
        else:
            print(f"✅ {name} already exists.")
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
        
        # 3. Handle Rerankers (Cross-Encoders)
        if "reranker" in name.lower() or "cross-encoder" in name.lower():
            framework = "ov" if "ov" in name.lower() else "pt"
            result = benchmark_reranker(name, local_path, framework=framework)
        else:
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
