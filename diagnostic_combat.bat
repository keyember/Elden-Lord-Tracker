@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%~dp0diagnostic_combat.py" %*
) else if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" "%~dp0diagnostic_combat.py" %*
) else (
    python "%~dp0diagnostic_combat.py" %*
)
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Le diagnostic a signale une erreur. Lis le message ci-dessus.
pause
exit /b %RESULT%
