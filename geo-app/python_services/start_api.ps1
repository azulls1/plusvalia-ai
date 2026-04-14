# Script para iniciar la API de FastAPI
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Iniciando API de Predicciones ML" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio de la API
Set-Location -Path $PSScriptRoot\api

# Iniciar el servidor
Write-Host "Ejecutando: python main.py" -ForegroundColor Yellow
Write-Host ""

python main.py

