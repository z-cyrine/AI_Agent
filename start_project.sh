#!/bin/bash

# 1. Activation de l'environnement Conda
# On utilise 'source' pour s'assurer que conda est reconnu dans le script
source ~/miniconda/etc/profile.d/conda.sh
conda activate ai_agent_env

if [ $? -eq 0 ]; then
    echo "Environnement ai_agent_env activé."
else
    echo "Échec de l'activation de l'environnement."
    exit 1
fi

#ENVIRONNEMENT AVEC CONDA
conda create -n ai_agent_env python=3.10 -y
conda activate ai_agent_env
#débloquer conda
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
#installation dépendances
pip install mcp fastmcp
pip install langchain-openai langchain-groq langgraph chromadb \
            sentence-transformers httpx pydantic tqdm flash-mcp
#tester main.py
python3 main.py --example 

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