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
