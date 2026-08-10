$ErrorActionPreference = "Stop"

$dir = Join-Path $PSScriptRoot "models\piper"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium"

Write-Host "Downloading Piper voice ru_RU-dmitri-medium into $dir ..."
Invoke-WebRequest -Uri "$base/ru_RU-dmitri-medium.onnx" -OutFile (Join-Path $dir "ru_RU-dmitri-medium.onnx")
Invoke-WebRequest -Uri "$base/ru_RU-dmitri-medium.onnx.json" -OutFile (Join-Path $dir "ru_RU-dmitri-medium.onnx.json")

Write-Host "Done. The faster-whisper 'small' model will download automatically on first run of server.py."
