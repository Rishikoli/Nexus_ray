@echo off
echo ========================================
echo Downloading Mistral Models via curl
echo ========================================
echo.

cd /d "d:\Intelfinal\Nexus_ray"

echo [1/3] Downloading FP16 Model Binary (14GB - this will take time)...
curl -L -C - --progress-bar -o "models\mistral-7b-fp16\openvino_model.bin" "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.bin"
echo.

echo [2/3] Downloading FP16 Model XML...
curl -L -C - --progress-bar -o "models\mistral-7b-fp16\openvino_model.xml" "https://huggingface.co/OpenVINO/Mistral-7B-Instruct-v0.2-fp16-ov/resolve/main/openvino_model.xml"
echo.

echo [3/3] Downloading INT8 Model Binary (7GB - this will take time)...
curl -L -C - --progress-bar -o "models\mistral-7b-int8\openvino_model.bin" "https://huggingface.co/OpenVINO/mistral-7b-instruct-v0.1-int8-ov/resolve/main/openvino_model.bin"
echo.

echo ========================================
echo Download Complete! Check file sizes:
echo ========================================
dir /s models\mistral-7b-fp16\*.bin
dir /s models\mistral-7b-int8\*.bin

pause
