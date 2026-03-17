#!/bin/bash

ORDER_ID="4922e86b-a079-46b6-95ba-c0adb8861761"

# Codes couleurs propres
# On utilise \x1b pour éviter les bugs d'interprétation de certains terminaux
CYAN='\x1b[36m'
GREEN='\x1b[32m'
YELLOW='\x1b[33m'
MAGENTA='\x1b[35m'
BLUE='\x1b[34m'
BOLD='\x1b[1m'
RESET='\x1b[0m'

echo "=========================================================="
echo -e "🔍 TRACE D'ORCHESTRATION : $ORDER_ID"
echo "=========================================================="

# Fonction de coloration par substitution de texte
colorize() {
    sed -u \
        -e "s/$ORDER_ID/${YELLOW}&${RESET}/g" \
        -e "s/INPROGRESS/${BOLD}${CYAN}&${RESET}/g" \
        -e "s/COMPLETED/${BOLD}${GREEN}&${RESET}/g" \
        -e "s/will set Service Order in progress/${BOLD}${YELLOW}&${RESET}/g" \
        -e "s/Service order is scheduled to start now/${BOLD}${GREEN}&${RESET}/g" \
        -e "s/will retrieve Service Order from catalog/${MAGENTA}&${RESET}/g" \
        -e "s/FindOrderItems/${BOLD}${MAGENTA}&${RESET}/g" \
        -e "s/Will updateServiceOrder/${BLUE}&${RESET}/g"
}

echo -e "\n1) [SCAPI] - Réception et Enregistrement :"
sudo docker logs openslice-scapi 2>&1 | grep --line-buffered "$ORDER_ID" | colorize

echo -e "\n2) [OSOM] - Orchestration et Workflow :"
sudo docker logs openslice-osom 2>&1 | grep --line-buffered "$ORDER_ID" | colorize