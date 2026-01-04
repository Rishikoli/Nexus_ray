# Enhanced download script with verbose output
Write-Host "🚀 Starting Enhanced Direct Downloads" -ForegroundColor Green
Write-Host "=" * 60

# Model FP16 - openvino_model.bin
$fp16_url = "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.bin"
$fp16_output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-fp16\openvino_model.bin"

# Model FP16 - openvino_model.xml  
$fp16_xml_url = "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.xml"
$fp16_xml_output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-fp16\openvino_model.xml"

# Model INT8 - openvino_model.bin
$int8_url = "https://huggingface.co/OpenVINO/mistral-7b-instruct-v0.1-int8-ov/resolve/main/openvino_model.bin"
$int8_output = "d:\Intelfinal\Nexus_ray\models\mistral-7b-int8\openvino_model.bin"

function Download-File {
    param(
        [string]$Url,
        [string]$Output,
        [string]$Name
    )
    
    Write-Host "`n📦 Downloading: $Name" -ForegroundColor Cyan
    Write-Host "   URL: $Url" -ForegroundColor Gray
    Write-Host "   Output: $Output" -ForegroundColor Gray
    
    # Check if exists
    if (Test-Path $Output) {
        $size = (Get-Item $Output).Length / 1GB
        if ($size -gt 1) {
            Write-Host "   ✅ File exists and is large enough ($([math]::Round($size, 2)) GB). Skipping." -ForegroundColor Green
            return $true
        } else {
            Write-Host "   ⚠️ File exists but is too small. Re-downloading..." -ForegroundColor Yellow
            Remove-Item $Output -Force
        }
    }
    
    # Ensure directory exists
    $dir = Split-Path $Output
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    Write-Host "   ⬇️ Starting download (this will take time for large files)..." -ForegroundColor Yellow
    
    try {
        # Use WebClient for better control
        $webClient = New-Object System.Net.WebClient
        
        # Add progress handler
        $EventDataComplete = Register-ObjectEvent $webClient DownloadProgressChanged -SourceIdentifier WebClient.DownloadProgressChanged -Action {
            $Global:downloadedBytes = $EventArgs.BytesReceived
            $Global:totalBytes = $EventArgs.TotalBytesToReceive
            if ($Global:totalBytes -gt 0) {
                $percent = [Math]::Round(($Global:downloadedBytes / $Global:totalBytes) * 100, 2)  
                Write-Host "`r   Progress: $percent% ($([Math]::Round($Global:downloadedBytes/1MB, 2)) MB / $([Math]::Round($Global:totalBytes/1MB, 2)) MB)" -NoNewline
            }
        }
        
        $webClient.DownloadFile($Url, $Output)
        
        Unregister-Event -SourceIdentifier WebClient.DownloadProgressChanged
        Remove-Job -Name WebClient.DownloadProgressChanged -Force -ErrorAction SilentlyContinue
        
        Write-Host ""
        $size = (Get-Item $Output).Length / 1GB
        Write-Host "   ✅ Download complete! Size: $([math]::Round($size, 2)) GB" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host ""
        Write-Host "   ❌ Download failed: $_" -ForegroundColor Red
        Write-Host "   Error details: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        if ($webClient) { $webClient.Dispose() }
    }
}

# Download FP16 XML (small file first to test)
Download-File -Url $fp16_xml_url -Output $fp16_xml_output -Name "FP16 Model XML"

# Download FP16 BIN
Download-File -Url $fp16_url -Output $fp16_output -Name "FP16 Model Binary"

# Download INT8 BIN
Download-File -Url $int8_url -Output $int8_output -Name "INT8 Model Binary"

Write-Host "`n✨ Download script complete!" -ForegroundColor Green
