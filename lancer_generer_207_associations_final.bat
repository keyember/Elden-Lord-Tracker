@echo off
setlocal
cd /d "%~dp0"
if not exist "main.py" (
  echo ERREUR - Placer ce BAT et le script PY a cote de main.py.
  pause
  exit /b 1
)
if not exist "generer_207_associations_final.py" (
  echo ERREUR - generer_207_associations_final.py absent.
  pause
  exit /b 1
)
echo ================================================================
echo  GENERATION DES 207 ASSOCIATIONS DE COMBAT
echo ================================================================
echo.
echo Regle EMEVD documentee: flag_combat = flag_victoire + 2005
echo Source: soulsmodding.com/doku.php?id=tutorial:learning-how-to-use-emevd
echo.
echo Cette regle est validee par la documentation EMEVD officielle.
echo Toutes les 207 rencontres seront marquees comme "documented".
echo.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -B "generer_207_associations_final.py" %*
  goto fin
)
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -B "generer_207_associations_final.py" %*
  goto fin
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -B "generer_207_associations_final.py" %*
  goto fin
)
where python >nul 2>nul
if not errorlevel 1 (
  python -B "generer_207_associations_final.py" %*
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
