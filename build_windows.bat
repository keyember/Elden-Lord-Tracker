@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 goto error
.venv\Scripts\python.exe -m unittest discover -s tests -v
if errorlevel 1 goto error
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name EldenRingTracker --add-data "overlay;overlay" --add-data "tracker/locales;tracker/locales" --add-data "tracker/catalogue_data;tracker/catalogue_data" main.py
if errorlevel 1 goto error
echo Application creee dans dist\EldenRingTracker. Conserver tout le dossier.
pause
exit /b 0
:error
echo Echec : consultez le message ci-dessus.
pause
exit /b 1
