@echo off
REM Script de vérification de l'installation - IBN Agentic AI Framework
REM Cyrine - Agents 1 & 2

echo ========================================
echo VERIFICATION DE L'INSTALLATION
echo ========================================
echo.

REM Vérifier Python
echo 1. Verification de Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)
echo    [OK] Python detecte
echo.

REM Vérifier pip
echo 2. Verification de pip...
pip --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] pip n'est pas installe
    pause
    exit /b 1
)
echo    [OK] pip detecte
echo.

REM Vérifier l'environnement virtuel
echo 3. Verification de l'environnement virtuel...
if exist "venv\Scripts\activate.bat" (
    echo    [OK] Environnement virtuel 'venv' existe
) else (
    echo    [INFO] Creation de l'environnement virtuel...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERREUR] Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
    echo    [OK] Environnement virtuel cree
)
echo.

REM Activer l'environnement virtuel
echo 4. Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo    [OK] Environnement virtuel active
echo.

REM Installer les dépendances
echo 5. Installation des dependances...
echo    Cela peut prendre quelques minutes...
pip install -q -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Erreur lors de l'installation des dependances
    pause
    exit /b 1
)
echo    [OK] Dependances installees
echo.

REM Vérifier le fichier .env
echo 6. Verification de la configuration...
if exist ".env" (
    echo    [OK] Fichier .env existe
) else (
    echo    [INFO] Creation du fichier .env depuis le template...
    copy .env.example .env
    echo    [ATTENTION] Editez le fichier .env et ajoutez votre cle API!
)
echo.

REM Créer le répertoire data si nécessaire
echo 7. Preparation des repertoires...
if not exist "data" mkdir data
if not exist "data\chroma_db" mkdir data\chroma_db
echo    [OK] Repertoires prets
echo.

REM Vérifier les imports Python critiques
echo 8. Verification des imports Python...
python -c "import langchain; import chromadb; import sentence_transformers; print('[OK] Imports critiques reussis')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Certains packages ne sont pas correctement installes
    echo    Reessayez: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.

echo ========================================
echo INSTALLATION VERIFIEE AVEC SUCCES!
echo ========================================
echo.
echo Prochaines etapes:
echo 1. Editer le fichier .env et ajouter votre cle API
echo 2. Executer: python scripts\ingest_catalog.py --mock
echo 3. Tester: python main.py --example
echo.
pause
