#!/bin/bash
# Activer le nouvel environnement virtuel avec SQLite 3.35.0

cd /home/ilef/Desktop/3A/AI_Agent

# Définir le chemin pour utiliser la nouvelle SQLite
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export PATH=/usr/local/bin:$PATH

# Activer l'environnement virtuel
source venv/bin/activate

echo "✅ Environnement activé avec SQLite 3.35.0"
sqlite3 --version
python3 -c "import sqlite3; print(f'Python SQLite: {sqlite3.sqlite_version}')"
