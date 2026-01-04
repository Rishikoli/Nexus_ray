from huggingface_hub import list_repo_files

MODELS = [
    "OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov",
    "OpenVINO/mistral-7b-instruct-v0.1-int8-ov"
]

print("🔍 Inspecting Repositories...")
for model_id in MODELS:
    print(f"\n📂 Repo: {model_id}")
    try:
        files = list_repo_files(repo_id=model_id)
        for f in files:
            if f.endswith(".bin") or f.endswith(".xml"):
                print(f"   - {f}")
    except Exception as e:
        print(f"   ❌ Error listing files: {e}")
