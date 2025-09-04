@echo off
REM Simple batch file to kill Claude Desktop processes
echo ===================================
echo   KILL CLAUDE DESKTOP PROCESSES
echo ===================================
echo.

echo Killing Claude Desktop processes...

REM Kill various possible Claude process names
taskkill /F /IM "Claude.exe" 2>nul
taskkill /F /IM "ClaudeDesktop.exe" 2>nul
taskkill /F /IM "claude.exe" 2>nul

REM Kill any process with "claude" in the name
for /f "tokens=2 delims=," %%i in ('tasklist /fo csv ^| findstr /i "claude"') do (
    echo Found Claude process: %%i
    taskkill /F /PID %%i 2>nul
)

echo.
echo Waiting 2 seconds for processes to terminate...
timeout /t 2 /nobreak >nul

echo.
echo Checking for remaining Claude processes...
tasklist | findstr /i "claude" >nul
if %errorlevel%==0 (
    echo WARNING: Some Claude processes may still be running
    tasklist | findstr /i "claude"
) else (
    echo SUCCESS: All Claude Desktop processes terminated
)

echo.
echo You can now restart Claude Desktop to pick up MCP changes.
echo.
pause