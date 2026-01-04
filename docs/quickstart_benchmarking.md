# Quick Start: Benchmarking OpenVINO Models

Get performance metrics for Intel OpenVINO optimized models in under 5 minutes.

## Prerequisites

- Python 3.12+
- 16GB+ RAM recommended
- Models downloaded (FP16: 14GB, INT8: 7GB)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `optimum[openvino]` - Intel OpenVINO integration
- `transformers` - HuggingFace transformers
- `numpy` - NumPy for metrics
- `psutil` - System resource monitoring

## Step 2: Download Models

### Automated Download

```bash
# Windows
scripts\download_models.bat

# Or Python script
python scripts/verify_downloads.py
```

### Manual Download

If automated download fails, download directly from HuggingFace:

**FP16 Model:**
```bash
curl -L -C - -o models/mistral-7b-fp16/openvino_model.bin \
  https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.bin
```

**INT8 Model:**
```bash
curl -L -C - -o models/mistral-7b-int8/openvino_model.bin \
  https://huggingface.co/OpenVINO/mistral-7b-instruct-v0.1-int8-ov/resolve/main/openvino_model.bin
```

## Step 3: Verify Installation

```bash
python scripts/verify_downloads.py
```

Expected output:
```
✅ FP16 Model: All files present
✅ INT8 Model: All files present
```

## Step 4: Run Benchmark

```bash
python scripts/benchmark_models.py
```

This will:
1. Load both models sequentially
2. Run 6 test prompts on each
3. Measure performance metrics
4. Save results to `benchmark_results.json`

**Estimated time:** 10-15 minutes (depending on CPU)

## Step 5: View Results

```bash
cat benchmark_results.json
```

Example output:
```json
[
  {
    "model": "mistral-7b-int8",
    "avg_tokens_per_second": 14.5,
    "avg_latency_per_request": 3.2,
    "memory_mb": 7100
  },
  {
    "model": "mistral-7b-fp16",
    "avg_tokens_per_second": 7.8,
    "avg_latency_per_request": 6.5,
    "memory_mb": 14200
  }
]
```

## Understanding Results

### Key Metrics

| Metric | Description | Better Value |
|--------|-------------|--------------|
| `avg_tokens_per_second` | Generation throughput | Higher |
| `avg_latency_per_request` | Response time | Lower |
| `memory_mb` | RAM usage | Lower |
| `load_time` | Model load time | Lower |

### Expected Performance

INT8 vs FP16 Improvements:
- **2-3x faster** throughput
- **~50% lower** latency
- **~50% less** memory
- **~40% faster** load time

## Troubleshooting

### Model Download Issues

**Problem:** Download fails or stalls

**Solution:**
```bash
# Use resume-capable download
curl -L -C - --progress-bar -o <output> <url>

# Or use wget
wget -c <url> -O <output>
```

### Memory Errors

**Problem:** "Out of Memory" during inference

**Solution:**
- Close other applications
- Use INT8 model only (requires less RAM)
- Reduce `max_tokens` in benchmark script

### ImportError

**Problem:** `ModuleNotFoundError: No module named 'optimum'`

**Solution:**
```bash
pip install optimum[openvino] transformers
```

## Next Steps

- **Visualize Results**: Create charts with matplotlib/plotly
- **Custom Prompts**: Edit `PROMPTS` in `benchmark_models.py`
- **Production Use**: Integrate INT8 model into Nexus Ray workflows

## Support

- [Full Documentation](../docs/benchmarking.md)
- [GitHub Issues](https://github.com/nexus-ray/framework/issues)
