@echo off
chcp 65001 >nul
echo ============================================
echo   Correctif debug - Elden Lord Tracker
echo ============================================
echo.
echo [INFO] Application du correctif...
echo.
python appliquer_correctif.py
if errorlevel 1 (
    echo.
    echo ERREUR: Le correctif a echoue.
    pause
    exit /b 1
)
echo.
echo ============================================
echo   Correctif applique avec succes!
echo ============================================
echo.
echo Pour tester en mode debug:
echo   python -B mettre_a_jour_lecture_catalogue.py --dry-run
echo.
echo Pour tester en mode normal:
echo   python -B mettre_a_jour_lecture_catalogue.py
echo.
pause
