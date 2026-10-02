@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (
  echo ERREUR - Placer ce BAT et les scripts PY a cote de main.py.
  pause
  exit /b 1
)
echo ==================================================================
echo  MISE A JOUR COMPLETE - TOUS LES 207 BOSSES
echo ==================================================================
echo.
echo Etape 1 - Correction de la validation (formatage LF/CRLF accepte)
echo Etape 2 - Generation automatique des 207 associations
echo.
if not exist "corriger_validation_lecture.py" (
  echo ERREUR - corriger_validation_lecture.py absent.
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
echo.
echo ETAPE 1/2 - Correction de validation...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "corriger_validation_lecture.py"
) else if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "corriger_validation_lecture.py"
) else if exist "py.exe" (
  py -3 -B "corriger_validation_lecture.py"
) else (
  python -B "corriger_validation_lecture.py"
)
if errorlevel 1 (
  echo.
  echo ERREUR - La correction de validation a echoue.
  pause
  exit /b 1
)
echo.
echo ETAPE 2/2 - Generation des 207 associations...
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "generer_207_associations.py"
) else if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "generer_207_associations.py"
) else if exist "py.exe" (
  py -3 -B "generer_207_associations.py"
) else (
  python -B "generer_207_associations.py"
)
if errorlevel 1 (
  echo.
  echo ERREUR - La generation des associations a echoue.
  pause
  exit /b 1
)
echo.
echo ==================================================================
echo  MISE A JOUR TERMINEE
echo ==================================================================
echo.
echo Prochaine etape : Lancer l'update du lecteur :
echo   lancer_update_lecture_catalogue.bat
echo   Choix 1 - Mettre a jour le lecteur du catalogue
echo   Puis taper APPLIQUER
echo.
echo Ensuite : Redemarrer le tracker pour voir les 207 bosses.
echo.
pause
exit /b 0
