@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (
  echo ERREUR - Placer ce BAT et le correctif PY a cote de main.py.
  pause
  exit /b 1
)
if not exist "corriger_validation_lecture.py" (
  echo ERREUR - corriger_validation_lecture.py absent.
  pause
  exit /b 1
)
if not exist "mettre_a_jour_lecture_catalogue.py" (
  echo ERREUR - Conserver mettre_a_jour_lecture_catalogue.py deja fourni a cote du correctif.
  pause
  exit /b 1
)
echo Correctif de validation - aucune logique memoire forcee.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "corriger_validation_lecture.py" %*
  goto fin
)
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "corriger_validation_lecture.py" %*
  goto fin
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -B "corriger_validation_lecture.py" %*
  goto fin
)
where python >nul 2>nul
if not errorlevel 1 (
  python -B "corriger_validation_lecture.py" %*
  goto fin
)
echo ERREUR - Aucun Python trouve. Utiliser le Python habituel du tracker.
pause
exit /b 1
:fin
set "code=%errorlevel%"
if not "%code%"=="0" echo Le correctif a signale une erreur. Lire les lignes ci-dessus.
pause
exit /b %code%
