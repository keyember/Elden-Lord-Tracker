@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (echo ERREUR & pause & exit /b 1)
if not exist "mettre_a_jour_lecture_catalogue_fix.py" (echo ERREUR & pause & exit /b 1)
if not exist "mettre_a_jour_lecture_catalogue.py" (echo ERREUR & pause & exit /b 1)
echo Correctif pour accepter SOURCE_BANK genere automatiquement.
python -B "mettre_a_jour_lecture_catalogue_fix.py"
if errorlevel 1 (echo ERREUR & pause & exit /b 1)
echo Prochaine etape: lancer_update_lecture_catalogue.bat -> Choix 1 -> APPLIQUER
pause
exit /b 0
