# Kill Claude Desktop Processes
# This script forcefully terminates all Claude Desktop related processes

Write-Host "=== CLAUDE DESKTOP PROCESS KILLER ===" -ForegroundColor Cyan
Write-Host ""

# List of possible Claude process names
$claudeProcesses = @(
    "Claude",
    "Claude Desktop", 
    "ClaudeDesktop",
    "claude.exe",
    "Claude.exe",
    "ClaudeDesktop.exe"
)

$processesKilled = 0
$totalProcessesFound = 0

Write-Host "Searching for Claude Desktop processes..." -ForegroundColor Yellow

# Check for each possible process name
foreach ($processName in $claudeProcesses) {
    try {
        $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
        
        if ($processes) {
            $count = ($processes | Measure-Object).Count
            $totalProcessesFound += $count
            
            Write-Host "Found $count process(es) named '$processName'" -ForegroundColor Green
            
            foreach ($process in $processes) {
                try {
                    Write-Host "  Killing PID $($process.Id) - $($process.ProcessName)" -ForegroundColor White
                    $process.Kill()
                    $processesKilled++
                    Start-Sleep -Milliseconds 100
                } catch {
                    Write-Host "  Failed to kill PID $($process.Id): $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    } catch {
        # Process name not found, continue silently
    }
}

# Also search for any process with "claude" in the name (case insensitive)
Write-Host ""
Write-Host "Searching for any processes containing 'claude'..." -ForegroundColor Yellow

try {
    $allProcesses = Get-Process | Where-Object { $_.ProcessName -match "claude" -or $_.MainWindowTitle -match "claude" }
    
    if ($allProcesses) {
        foreach ($process in $allProcesses) {
            try {
                Write-Host "  Found: PID $($process.Id) - $($process.ProcessName) - $($process.MainWindowTitle)" -ForegroundColor Green
                Write-Host "  Killing PID $($process.Id)" -ForegroundColor White
                $process.Kill()
                $processesKilled++
                $totalProcessesFound++
                Start-Sleep -Milliseconds 100
            } catch {
                Write-Host "  Failed to kill PID $($process.Id): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
} catch {
    Write-Host "Error searching for processes: $($_.Exception.Message)" -ForegroundColor Red
}

# Final summary
Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan

if ($totalProcessesFound -eq 0) {
    Write-Host "No Claude Desktop processes found running." -ForegroundColor Green
} else {
    Write-Host "Total processes found: $totalProcessesFound" -ForegroundColor Yellow
    Write-Host "Total processes killed: $processesKilled" -ForegroundColor $(if ($processesKilled -eq $totalProcessesFound) { "Green" } else { "Yellow" })
}

# Wait a moment for processes to fully terminate
Write-Host ""
Write-Host "Waiting 2 seconds for processes to fully terminate..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# Verify no Claude processes are still running
Write-Host ""
Write-Host "Verifying all Claude processes are terminated..." -ForegroundColor Yellow

$remainingProcesses = Get-Process | Where-Object { 
    $_.ProcessName -match "claude" -or 
    $_.MainWindowTitle -match "claude" -or
    $_.ProcessName -eq "Claude" -or
    $_.ProcessName -eq "ClaudeDesktop"
}

if ($remainingProcesses) {
    Write-Host "WARNING: Some Claude processes may still be running:" -ForegroundColor Red
    foreach ($process in $remainingProcesses) {
        Write-Host "  PID $($process.Id) - $($process.ProcessName)" -ForegroundColor Red
    }
} else {
    Write-Host "SUCCESS: All Claude Desktop processes have been terminated." -ForegroundColor Green
}

Write-Host ""
Write-Host "You can now restart Claude Desktop to pick up MCP server changes." -ForegroundColor Cyan
Write-Host ""

# Optional: Ask if user wants to start Claude Desktop
$startClaude = Read-Host "Do you want to start Claude Desktop now? (y/n)"
if ($startClaude -eq "y" -or $startClaude -eq "Y" -or $startClaude -eq "yes") {
    Write-Host "Starting Claude Desktop..." -ForegroundColor Green
    
    # Try common Claude Desktop installation paths
    $claudePaths = @(
        "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
        "$env:PROGRAMFILES\Claude\Claude.exe",
        "${env:PROGRAMFILES(X86)}\Claude\Claude.exe"
    )
    
    $claudeStarted = $false
    foreach ($path in $claudePaths) {
        if (Test-Path $path) {
            Write-Host "Found Claude Desktop at: $path" -ForegroundColor Green
            try {
                Start-Process $path
                $claudeStarted = $true
                Write-Host "Claude Desktop started successfully!" -ForegroundColor Green
                break
            } catch {
                Write-Host "Failed to start Claude Desktop: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    if (-not $claudeStarted) {
        Write-Host "Could not find Claude Desktop executable. Please start it manually." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Script completed." -ForegroundColor Cyan