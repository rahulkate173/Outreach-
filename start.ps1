# Single script: install deps -> Ollama load/run -> server start -> frontend opens in browser.
# Run: .\start.ps1
# Requires: Ollama (https://ollama.com), Python with pip

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

# ---- 1. Install dependencies ----
Write-Host "[1/4] Checking dependencies..." -ForegroundColor Cyan
if (-not (Test-Path ".\venv" -PathType Container)) {
    Write-Host "      Creating venv and installing packages..."
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt -q
} else {
    & .\venv\Scripts\Activate.ps1
}
Write-Host "      Dependencies OK." -ForegroundColor Green

# ---- 2. Find Ollama executable: PATH first, then common install locations ----
$ollamaExe = $null
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    $ollamaExe = $ollamaCmd.Source
} else {
    $pathsToCheck = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Ollama\ollama.exe")
    )
    foreach ($p in $pathsToCheck) {
        if ($p -and (Test-Path $p)) {
            $ollamaExe = $p
            Write-Host "      Found Ollama at: $ollamaExe" -ForegroundColor Gray
            break
        }
    }
}

# ---- 2. Ollama: load and run ----
Write-Host "[2/4] Checking Ollama..." -ForegroundColor Cyan
$ollamaRunning = $false
try {
    $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    $ollamaRunning = $true
    Write-Host "      Ollama is already running." -ForegroundColor Green
} catch {}

if (-not $ollamaRunning) {
    if (-not $ollamaExe) {
        Write-Host "      Ollama not found." -ForegroundColor Yellow
        Write-Host "      Why: Ollama is not installed, or not in PATH / default install folder." -ForegroundColor Gray
        Write-Host ""
        $download = "N"
        try {
            $download = Read-Host "      Download Ollama installer from web and run it now? (Y/N)"
        } catch {}
        if ($download -eq "Y" -or $download -eq "y") {
            $installerUrl = "https://ollama.com/download/OllamaSetup.exe"
            $installerPath = Join-Path $env:TEMP "OllamaSetup.exe"
            Write-Host "      Downloading from $installerUrl ..." -ForegroundColor Cyan
            try {
                Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
                Write-Host "      Running installer. Complete the setup, then run .\start.ps1 again." -ForegroundColor Green
                Start-Process -FilePath $installerPath -Wait
            } catch {
                Write-Host "      Download failed. Install manually from https://ollama.com" -ForegroundColor Yellow
            }
        } else {
            Write-Host "      Install from https://ollama.com then restart terminal and run .\start.ps1 again." -ForegroundColor Cyan
        }
        Write-Host "      Starting app anyway (generate outreach works after Ollama is installed)." -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "      Starting Ollama in background..." -ForegroundColor Gray
        Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
        # Wait for Ollama API to be ready (up to 30 seconds)
        $waited = 0
        while ($waited -lt 30) {
            Start-Sleep -Seconds 2
            $waited += 2
            try {
                $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
                $ollamaRunning = $true
                Write-Host "      Ollama is up." -ForegroundColor Green
                break
            } catch {}
        }
        if (-not $ollamaRunning) {
            Write-Host "      Ollama did not start in time. Run manually: & '$ollamaExe' serve" -ForegroundColor Yellow
        }
    }
}

# ---- 3. Pull model when Ollama is available (ollama pull phi3:mini - small, fast) ----
if ($ollamaRunning) {
    Write-Host "[3/4] Pulling model phi3:mini from web (small, fast download)..." -ForegroundColor Cyan
    if ($ollamaExe) {
        & $ollamaExe pull phi3:mini
        if ($LASTEXITCODE -ne 0) {
            Write-Host "      Pull failed. You can run: ollama pull phi3:mini" -ForegroundColor Yellow
        } else {
            Write-Host "      Model phi3:mini OK." -ForegroundColor Green
        }
    } else {
        python scripts/ensure_model.py
        if ($LASTEXITCODE -ne 0) {
            Write-Host "      Model check failed. Run: ollama pull phi3:mini" -ForegroundColor Yellow
        } else {
            Write-Host "      Model OK." -ForegroundColor Green
        }
    }
} else {
    Write-Host "[3/4] Skipping model (Ollama not running). Run .\start.ps1 after installing Ollama." -ForegroundColor Gray
}

# ---- 4. Start server and open frontend in browser ----
Write-Host "[4/4] Starting server and opening frontend..." -ForegroundColor Cyan
Write-Host "      Server: http://localhost:8000 (browser will open automatically)" -ForegroundColor Gray
python run.py
