# Script PowerShell de vérification de l'installation
# IBN Agentic AI Framework - (Agents 1 & 2)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION DE L'INSTALLATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier Python
Write-Host "1. Verification de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   [ERREUR] Python n'est pas installe ou pas dans le PATH" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Vérifier pip
Write-Host "2. Verification de pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "   [OK] pip detecte" -ForegroundColor Green
} catch {
    Write-Host "   [ERREUR] pip n'est pas installe" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Vérifier/Créer l'environnement virtuel
Write-Host "3. Verification de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   [OK] Environnement virtuel 'venv' existe" -ForegroundColor Green
} else {
    Write-Host "   [INFO] Creation de l'environnement virtuel..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [ERREUR] Impossible de creer l'environnement virtuel" -ForegroundColor Red
        exit 1
    }
    Write-Host "   [OK] Environnement virtuel cree" -ForegroundColor Green
}
Write-Host ""

# 4. Activer l'environnement virtuel
Write-Host "4. Activation de l'environnement virtuel..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "   [OK] Environnement virtuel active" -ForegroundColor Green
Write-Host ""

# 5. Installer les dépendances
Write-Host "5. Installation des dependances..." -ForegroundColor Yellow
Write-Host "   Cela peut prendre quelques minutes..." -ForegroundColor Cyan
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "   [ERREUR] Erreur lors de l'installation des dependances" -ForegroundColor Red
    exit 1
}
Write-Host "   [OK] Dependances installees" -ForegroundColor Green
Write-Host ""

# 6. Vérifier le fichier .env
Write-Host "6. Verification de la configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   [OK] Fichier .env existe" -ForegroundColor Green
} else {
    Write-Host "   [INFO] Creation du fichier .env depuis le template..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "   [ATTENTION] Editez le fichier .env et ajoutez votre cle API!" -ForegroundColor Yellow
}
Write-Host ""

# 7. Créer les répertoires nécessaires
Write-Host "7. Preparation des repertoires..." -ForegroundColor Yellow
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" | Out-Null }
if (-not (Test-Path "data\chroma_db")) { New-Item -ItemType Directory -Path "data\chroma_db" | Out-Null }
Write-Host "   [OK] Repertoires prets" -ForegroundColor Green
Write-Host ""

# 8. Vérifier les imports Python critiques
Write-Host "8. Verification des imports Python..." -ForegroundColor Yellow
$importTest = python -c "import langchain; import chromadb; import sentence_transformers; print('[OK]')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   [ERREUR] Certains packages ne sont pas correctement installes" -ForegroundColor Red
    Write-Host "   Reessayez: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] Imports critiques reussis" -ForegroundColor Green
Write-Host ""

# Succès
Write-Host "========================================" -ForegroundColor Green
Write-Host "INSTALLATION VERIFIEE AVEC SUCCES!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines etapes:" -ForegroundColor Cyan
Write-Host "1. Editer le fichier .env et ajouter votre cle API" -ForegroundColor White
Write-Host "2. Executer: python scripts\ingest_catalog.py --mock" -ForegroundColor White
Write-Host "3. Tester: python main.py --example" -ForegroundColor White
Write-Host ""
