@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (
  echo ERREUR - Placer ce BAT et le script PY a cote de main.py.
  pause
  exit /b 1
)
if not exist "generer_207_associations.py" (
  echo ERREUR - generer_207_associations.py absent.
  pause
  exit /b 1
)
if not exist "audit_flags\rapprochement-207-rencontres.csv" (
  echo ERREUR - Le CSV de rapprochement est requis dans audit_flags\.
  pause
  exit /b 1
)
echo Generation automatique des 207 associations...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "generer_207_associations.py" %*
  goto fin
)
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "generer_207_associations.py" %*
  goto fin
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -B "generer_207_associations.py" %*
  goto fin
)
where python >nul 2>nul
if not errorlevel 1 (
  python -B "generer_207_associations.py" %*
  goto fin
)
echo ERREUR - Aucun Python trouve.
pause
exit /b 1
:fin
set "code=%errorlevel%"
if not "%code%"=="0" echo Le script a signale une erreur. Lire les lignes ci-dessus.
pause
exit /b %code%
