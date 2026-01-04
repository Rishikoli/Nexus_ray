print("1. Imports starting...")
import time
import json
import psutil
print("2. psutil imported")
try:
    import numpy as np
    print("3. numpy imported")
except Exception as e:
    print(f"3. numpy failed: {e}")

try:
    from optimum.intel import OVModelForCausalLM
    print("4. optimum-intel imported")
except Exception as e:
    print(f"4. optimum-intel failed: {e}")

from transformers import AutoTokenizer
print("5. transformers imported")

print("🏁 Initialization test complete.")
