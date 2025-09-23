# PowerShell script to start the Bloomberg system
# Run this from the BloombergGPT folder

Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host "🌟 Bloomberg Natural Language Interface" -ForegroundColor Cyan
Write-Host "   Single Command Launcher" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes
Write-Host "🧹 Cleaning up old processes..." -ForegroundColor Yellow
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Stop-Process -Name ngrok -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start main server
Write-Host "🚀 Starting Bloomberg Data Broker..." -ForegroundColor Green
$server = Start-Process -FilePath "python" -ArgumentList "main.py" -PassThru -WindowStyle Normal
Write-Host "✅ Main server started (PID: $($server.Id))" -ForegroundColor Green

# Wait for server to start
Write-Host "⏳ Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start ngrok
Write-Host "🚇 Starting ngrok tunnel..." -ForegroundColor Green
$ngrok = Start-Process -FilePath "python" -ArgumentList "start_ngrok.py" -PassThru -WindowStyle Normal
Write-Host "✅ ngrok started (PID: $($ngrok.Id))" -ForegroundColor Green

Write-Host ""
Write-Host "📊 System Status:" -ForegroundColor Cyan
Write-Host "-" * 30 -ForegroundColor Cyan
Write-Host "✅ Main server: RUNNING on http://localhost:8000" -ForegroundColor Green
Write-Host "✅ ngrok tunnel: RUNNING (check the ngrok window for URL)" -ForegroundColor Green

Write-Host ""
Write-Host "🌐 API Endpoints:" -ForegroundColor Cyan
Write-Host "   - http://localhost:8000/blp/fields" -ForegroundColor White
Write-Host "   - http://localhost:8000/blp/nlquery?query=Apple+stock+price" -ForegroundColor White

Write-Host ""
Write-Host "🎉 System started successfully!" -ForegroundColor Green
Write-Host "📝 Check the terminal windows for server and ngrok output" -ForegroundColor Yellow
Write-Host "🔍 Use Ctrl+C to stop everything" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
