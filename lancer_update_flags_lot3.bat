@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (
  echo ERREUR - Placer le PY et ce BAT a cote de main.py.
  pause
  exit /b 1
)
if not exist "mettre_a_jour_flags_lot3.py" (
  echo ERREUR - mettre_a_jour_flags_lot3.py absent.
  pause
  exit /b 1
)
echo Update hors ligne - moteur, lecteur et overlay conserves.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "mettre_a_jour_flags_lot3.py" %*
  goto fin
)
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "mettre_a_jour_flags_lot3.py" %*
  goto fin
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -B "mettre_a_jour_flags_lot3.py" %*
  goto fin
)
where python >nul 2>nul
if not errorlevel 1 (
  python -B "mettre_a_jour_flags_lot3.py" %*
  goto fin
)
echo ERREUR - Aucun Python trouve. Utiliser le Python deja utilise par lancer.bat.
pause
exit /b 1
:fin
set "code=%errorlevel%"
if not "%code%"=="0" echo L'update a signale une erreur - lire le message ci-dessus.
pause
exit /b %code%
