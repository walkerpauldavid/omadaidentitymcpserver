@echo off
REM Quick test batch file for Calculated Assignments
REM Usage: test_assignments.bat [identity_id]
REM Example: test_assignments.bat 1006715
REM 
REM Shows: Identity Name, Resource Names, Resource Types, IDs

echo ==================================================
echo   CALCULATED ASSIGNMENTS QUICK TEST
echo   Shows Resource Names, Types, and IDs
echo ==================================================

if "%1"=="" (
    echo Using default Identity ID: 1006500
    python quick_test_assignments.py
) else (
    echo Using Identity ID: %1
    python quick_test_assignments.py %1
)

echo.
echo ==================================================
echo   TEST COMPLETE
echo ==================================================
pause