# Direct download script using curl for HuggingFace models
# This bypasses Python library issues

$models = @(
    @{
        name = "mistral-7b-fp16"
        url = "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.bin"
        output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-fp16\openvino_model.bin"
    },
    @{
        name = "mistral-7b-fp16-xml"
        url = "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.xml"
        output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-fp16\openvino_model.xml"
    },
    @{
        name = "mistral-7b-int8"
        url = "https://huggingface.co/OpenVINO/mistral-7b-instruct-v0.1-int8-ov/resolve/main/openvino_model.bin"
        output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-int8\openvino_model.bin"
    }
)

Write-Host "🚀 Starting Direct CDN Downloads..." -ForegroundColor Green

foreach ($model in $models) {
    Write-Host "`n📦 Downloading $($model.name)..." -ForegroundColor Cyan
    Write-Host "   URL: $($model.url)" -ForegroundColor Gray
    Write-Host "   Target: $($model.output)" -ForegroundColor Gray
    
    # Check if file already exists
    if (Test-Path $model.output) {
        $size = (Get-Item $model.output).Length / 1GB
        Write-Host "   ✅ File exists ($([math]::Round($size, 2)) GB). Skipping." -ForegroundColor Green
        continue
    }
    
    # Create directory if it doesn't exist
    $dir = Split-Path $model.output
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    # Download with curl (supports resume with -C -)
    Write-Host "   ⬇️ Downloading (this may take a while)..." -ForegroundColor Yellow
    
    # Using Invoke-WebRequest with resume support
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $model.url -OutFile $model.output -Resume
        
        $size = (Get-Item $model.output).Length / 1GB
        Write-Host "   ✅ Downloaded successfully! Size: $([math]::Round($size, 2)) GB" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ Download failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n✨ Download process complete!" -ForegroundColor Green
