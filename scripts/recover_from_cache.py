import os
import shutil
from pathlib import Path

# Paths
MODELS_DIR = Path("d:/Intelfinal/Nexus_ray/models")
HF_CACHE = Path(os.path.expanduser("~/.cache/huggingface"))

MODELS = {
    "mistral-7b-fp16": {
        "repo": "OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov",
        "needed": ["openvino_model.bin", "openvino_model.xml"]
    },
    "mistral-7b-int8": {
        "repo": "OpenVINO/mistral-7b-instruct-v0.1-int8-ov",
        "needed": ["openvino_model.bin"]
    }
}

def find_in_cache(filename, min_size_mb=100):
    """Search for files in HuggingFace cache"""
    print(f"🔍 Searching cache for: {filename} (min {min_size_mb}MB)")
    
    if not HF_CACHE.exists():
        print(f"   ❌ Cache not found at {HF_CACHE}")
        return None
    
    # Search in hub cache
    hub_cache = HF_CACHE / "hub"
    if hub_cache.exists():
        for root, dirs, files in os.walk(hub_cache):
            for file in files:
                if filename in file or file == filename:
                    file_path = Path(root) / file
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb >= min_size_mb:
                        print(f"   ✅ Found: {file_path} ({size_mb:.2f} MB)")
                        return file_path
                    else:
                        print(f"   ⚠️ Found but too small: {file_path} ({size_mb:.2f} MB)")
    
    return None

def copy_or_link(source, dest):
    """Copy file from cache to destination"""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        if dest.exists():
            dest_size = dest.stat().st_size / (1024 * 1024)
            source_size = source.stat().st_size / (1024 * 1024)
            
            if dest_size >= source_size * 0.99:  # Allow 1% difference
                print(f"   ✅ Destination already has good file ({dest_size:.2f} MB)")
                return True
        
        print(f"   📋 Copying {source.name}...")
        shutil.copy2(source, dest)
        print(f"   ✅ Copied successfully!")
        return True
    except Exception as e:
        print(f"   ❌ Failed to copy: {e}")
        return False

def main():
    print("🚀 Cache Recovery Script")
    print("=" * 60)
    
    for model_name, info in MODELS.items():
        print(f"\n📦 Processing: {model_name}")
        model_dir = MODELS_DIR / model_name
        
        for filename in info["needed"]:
            dest = model_dir / filename
            
            # Check if already exists and is large enough
            if dest.exists():
                size_mb = dest.stat().st_size / (1024 * 1024)
                expected_size = 10000 if "bin" in filename else 1
                
                if size_mb >= expected_size:
                    print(f"   ✅ {filename} already complete ({size_mb:.2f} MB)")
                    continue
                else:
                    print(f"   ⚠️ {filename} exists but incomplete ({size_mb:.2f} MB)")
            
            # Search cache
            cached_file = find_in_cache(filename, min_size_mb=10 if "bin" in filename else 0.1)
            
            if cached_file:
                copy_or_link(cached_file, dest)
            else:
                print(f"   ❌ {filename} not found in cache. Needs download.")
    
    print("\n✨ Cache recovery complete!")

if __name__ == "__main__":
    main()
