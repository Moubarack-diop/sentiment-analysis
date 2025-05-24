@echo off
echo ========================================================
echo    Lanceur du projet d'analyse de sentiment en temps reel
echo ========================================================
echo.

REM Verifier si Python est installe
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.8+ et reessayer.
    pause
    exit /b 1
)

REM Verifier si Docker est installe
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Docker n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Docker Desktop pour Windows et reessayer.
    pause
    exit /b 1
)

REM Installer les dependances necessaires
echo Installation des dependances Python...
pip install multiprocessing logging webbrowser

REM Lancer le script Python
echo Lancement du projet...
python run_project.py

REM En cas d'erreur
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors de l'execution du projet.
    echo Consultez les logs pour plus de details.
    pause
)

pause 