import os
from pathlib import Path
from huggingface_hub import hf_hub_download

MODELS = {
    "mistral-7b-fp16": "OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov",
    "mistral-7b-int8": "OpenVINO/mistral-7b-instruct-v0.1-int8-ov"
}

REQUIRED_FILES = [
    "openvino_model.bin",
    "openvino_model.xml",
    "openvino_tokenizer.bin",
    "openvino_tokenizer.xml",
    "openvino_detokenizer.bin",
    "openvino_detokenizer.xml",
    "tokenizer_config.json",
    "tokenizer.json",
    "special_tokens_map.json",
    "config.json"
]

BASE_DIR = Path("d:/Intelfinal/Nexus_ray/models")

def check_and_download():
    print("🚀 Verifying Model Integrity...")
    
    for local_name, repo_id in MODELS.items():
        print(f"\n📦 Checking {local_name} ({repo_id})...")
        local_dir = BASE_DIR / local_name
        local_dir.mkdir(parents=True, exist_ok=True)
        
        missing_files = []
        for filename in REQUIRED_FILES:
            file_path = local_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
                print(f"   ❌ Missing: {filename}")
            else:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"   ✅ Found: {filename} ({size_mb:.2f} MB)")

        if not missing_files:
            print(f"   ✨ All files present for {local_name}!")
            continue
            
        print(f"   ⬇️ Downloading {len(missing_files)} missing files...")
        for filename in missing_files:
            print(f"      Downloading {filename}...")
            try:
                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=local_dir,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                print(f"      ✅ Downloaded {filename}")
            except Exception as e:
                print(f"      ❌ Failed to download {filename}: {e}")

if __name__ == "__main__":
    check_and_download()
