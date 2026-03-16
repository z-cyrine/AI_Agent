#!/bin/bash

echo "-------------------------------------------------------"
echo "🌐 Initialisation du Projet IBN - OpenSlice"
echo "-------------------------------------------------------"

# 1. Activation de l'environnement Conda
# On utilise 'source' pour s'assurer que conda est reconnu dans le script
source ~/miniconda/etc/profile.d/conda.sh
conda activate ai_agent_env

if [ $? -eq 0 ]; then
    echo "✅ Environnement ai_agent_env activé."
else
    echo "❌ Échec de l'activation de l'environnement."
    exit 1
fi

# 2. Vérification rapide des containers Docker (OpenSlice)
echo "🔍 Vérification de la connectivité OpenSlice..."
curl -s --connect-timeout 2 http://localhost:13082/tmf-api/serviceCatalogManagement/v4/serviceSpecification > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ OpenSlice est accessible."
    # 3. Lancement du test global
    python run_project_test.py
else
    echo "⚠️  OpenSlice (Docker) semble injoignable sur le port 13082."
    echo "👉 Lancez vos containers avant de continuer."
fi