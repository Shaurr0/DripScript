# FitCheck - Wardrobe AI Setup Script
Write-Host "Setting up FitCheck - Wardrobe AI..." -ForegroundColor Cyan

# Check Node.js
Write-Host "`nChecking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found. Please install Node.js 16+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check Python
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ from https://python.org/" -ForegroundColor Red
    exit 1
}

# Frontend Setup
Write-Host "`nSetting up Frontend (React + Vite)..." -ForegroundColor Cyan
Set-Location frontend
try {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host "Frontend dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}

# Backend Setup
Write-Host "`nSetting up Backend (Python)..." -ForegroundColor Cyan
Set-Location ..\backend
try {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install -r config/requirements.txt
    Write-Host "Backend dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install backend dependencies" -ForegroundColor Red
    Write-Host "Note: Backend is optional for demo mode" -ForegroundColor Yellow
}

# Back to root
Set-Location ..

# Create development scripts
Write-Host "`nCreating development scripts..." -ForegroundColor Cyan

# Frontend dev script
$frontendScript = @"
# Start Frontend Development Server
Write-Host "Starting FitCheck Frontend..." -ForegroundColor Cyan
Set-Location frontend
npm run dev
"@
Set-Content -Path "start-frontend.ps1" -Value $frontendScript

# Backend dev script  
$backendScript = @"
# Start Backend Development Server
Write-Host "Starting FitCheck Backend..." -ForegroundColor Cyan
Set-Location backend
python api/server.py
"@
Set-Content -Path "start-backend.ps1" -Value $backendScript

# Complete setup script
$completeScript = @"
# Start Complete Development Environment
Write-Host "Starting FitCheck - Complete Environment..." -ForegroundColor Cyan

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-File", "start-frontend.ps1"

# Wait a bit then start backend
Start-Sleep 3
Start-Process powershell -ArgumentList "-NoExit", "-File", "start-backend.ps1"

Write-Host "Both frontend and backend started!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend: http://localhost:5000" -ForegroundColor Yellow
"@
Set-Content -Path "start-complete.ps1" -Value $completeScript

Write-Host "`nSetup Complete!" -ForegroundColor Green
Write-Host "`nQuick Start Options:" -ForegroundColor Cyan
Write-Host "1. Frontend Only (Demo Mode): .\start-frontend.ps1" -ForegroundColor Yellow
Write-Host "2. Complete Environment: .\start-complete.ps1" -ForegroundColor Yellow
Write-Host "`nAfter starting, visit: http://localhost:5173" -ForegroundColor Green
Write-Host "Check README.md for detailed instructions" -ForegroundColor Gray

Write-Host "`nReady for hackathon demo!" -ForegroundColor Magenta