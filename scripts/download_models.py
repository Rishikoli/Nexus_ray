import os
from pathlib import Path
from huggingface_hub import snapshot_download

# Configuration from Notebook
MODELS = {
    # Using the IDs specifically found in the user's provided notebook
    "mistral-7b-fp16": "OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov",
    "mistral-7b-int8": "OpenVINO/mistral-7b-instruct-v0.1-int8-ov"
}

# Adjusted to project structure
MODEL_DIR = Path("d:/Intelfinal/Nexus_ray/models")

def main():
    print("🚀 Starting Model Installation (from Notebook spec)")
    print("-------------------------------------------------")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    for local_name, hf_id in MODELS.items():
        local_dir = MODEL_DIR / local_name
        
        print(f"\n📦 Processing {local_name}...")
        print(f"   Source: {hf_id}")
        print(f"   Target: {local_dir}")

        if local_dir.exists() and (local_dir / "openvino_model.xml").exists() and (local_dir / "openvino_model.bin").exists():
             print(f"   ✅ Already exists (XML + BIN). Skipping.")
             continue
        
        try:
            print(f"   ⬇️ Downloading snapshot (RESUMING)...")
            snapshot_download(repo_id=hf_id, local_dir=local_dir, force_download=False, resume_download=True)
            print(f"   ✅ Download complete.")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print("\n✨ All models processed!")

if __name__ == "__main__":
    main()
