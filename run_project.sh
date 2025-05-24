#!/bin/bash

echo "========================================================"
echo "    Lanceur du projet d'analyse de sentiment en temps réel"
echo "========================================================"
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé."
    echo "Veuillez installer Python 3.8+ et réessayer."
    exit 1
fi

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "ERREUR: Docker n'est pas installé."
    echo "Veuillez installer Docker et réessayer."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "ERREUR: Docker Compose n'est pas installé."
    echo "Veuillez installer Docker Compose et réessayer."
    exit 1
fi

# Rendre le script de soumission Spark exécutable
chmod +x scripts/submit_spark_job.sh

# Installer les dépendances nécessaires
echo "Installation des dépendances Python..."
pip3 install multiprocessing logging webbrowser

# Lancer le script Python
echo "Lancement du projet..."
python3 run_project.py

# En cas d'erreur
if [ $? -ne 0 ]; then
    echo
    echo "Une erreur s'est produite lors de l'exécution du projet."
    echo "Consultez les logs pour plus de détails."
fi 