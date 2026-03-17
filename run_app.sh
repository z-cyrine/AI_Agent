#!/bin/bash

# Script pour lancer l'interface Streamlit du Pipeline IBN

echo "🚀 Lancement de l'interface Pipeline IBN..."
echo ""
echo "L'application s'ouvrira sur http://localhost:8501"
echo ""
echo "Pour arrêter l'application, appuyez sur Ctrl+C"
echo ""

# Vérifier que Streamlit est installé
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit n'est pas installé."
    echo "Installation en cours..."
    pip install streamlit>=1.28.0 pandas>=2.0.0
fi

# Lancer l'application Streamlit
python -m streamlit run app.py --server.port 8501