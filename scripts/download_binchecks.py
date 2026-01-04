from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

# Configuration
MODELS = {
    "mistral-7b-fp16": {
        "repo": "OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov",
        "filename": "openvino_model.bin"
    },
    "mistral-7b-int8": {
        "repo": "OpenVINO/mistral-7b-instruct-v0.1-int8-ov",
        "filename": "openvino_model.bin"
    }
}

MODEL_DIR = Path("d:/Intelfinal/Nexus_ray/models")

def download_file(repo, filename, local_dir):
    print(f"⬇️ Downloading {filename} from {repo}...")
    try:
        # Download to cache
        cached_path = hf_hub_download(repo_id=repo, filename=filename, local_dir=local_dir, local_dir_use_symlinks=False, resume_download=True)
        print(f"✅ Successfully downloaded {filename} to {cached_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

def main():
    print("🚀 Starting Single File Recovery")
    
    for name, info in MODELS.items():
        local_dir = MODEL_DIR / name
        target_file = local_dir / info["filename"]
        
        if target_file.exists():
            print(f"✅ {name}/{info['filename']} already exists. Size: {target_file.stat().st_size / 1e9:.2f} GB")
            continue
            
        print(f"\n📦 Processing {name}...")
        download_file(info["repo"], info["filename"], local_dir)

if __name__ == "__main__":
    main()
