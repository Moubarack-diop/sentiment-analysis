#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import subprocess
from multiprocessing import Process

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_docker_services():
    """Démarre tous les services Docker via Docker Compose"""
    logger.info("Démarrage des services Docker (Kafka, Zookeeper, Elasticsearch, etc.)...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        # Attente pour l'initialisation des services
        logger.info("Attente de 30 secondes pour l'initialisation des services...")
        time.sleep(30)
        
        # Vérifier que les services sont bien démarrés
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True, check=True)
        logger.info("Services démarrés:\n%s", result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Erreur lors du démarrage des services Docker: %s", e)
        return False

def start_tweet_producer():
    """Démarre le producteur de tweets manuellement (au cas où le container ne démarre pas automatiquement)"""
    logger.info("Démarrage du producteur de tweets...")
    try:
        # Utiliser subprocess pour exécuter le producteur dans son container
        subprocess.run([
            "docker", "exec", "-d", "python-producer", 
            "python", "/app/tweet_producer.py"
        ], check=True)
        
        logger.info("Producteur de tweets démarré avec succès")
        
        # Boucle pour garder le processus actif et surveiller les logs
        while True:
            logs = subprocess.run(
                ["docker", "logs", "--tail", "10", "python-producer"],
                capture_output=True, text=True
            )
            logger.info("Derniers logs du producteur de tweets:\n%s", logs.stdout)
            time.sleep(30)  # Vérifier les logs toutes les 30 secondes
    
    except subprocess.CalledProcessError as e:
        logger.error("Erreur lors du démarrage du producteur de tweets: %s", e)
    except KeyboardInterrupt:
        logger.info("Arrêt du processus de producteur de tweets")

def start_spark_job():
    """Démarre le job Spark d'analyse de sentiment"""
    logger.info("Démarrage du job Spark d'analyse de sentiment...")
    try:
        # Installer les dépendances Python dans le conteneur Spark
        subprocess.run([
            "docker", "exec", "spark-master", "pip", "install", "elasticsearch", "nltk"
        ], check=True)
        
        logger.info("Dépendances Python installées avec succès")
        
        # Exécuter le script shell de soumission Spark
        if os.name == 'nt':  # Windows
            subprocess.run([
                "docker", "exec", "spark-master",
                "/opt/bitnami/spark/bin/spark-submit",
                "--master", "spark://spark-master:7077",
                "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1",
                "--conf", "spark.jars.ivy=/tmp/.ivy",
                "--conf", "spark.hadoop.hadoop.security.authentication=simple",
                "--conf", "spark.hadoop.hadoop.security.authorization=false",
                "/opt/bitnami/spark/consumer/sentiment_analyzer.py"
            ], check=True)
        else:  # Unix/Linux
            subprocess.run(["bash", "./scripts/submit_spark_job.sh"], check=True)
        
        logger.info("Job Spark démarré avec succès")
        
        # Surveiller les logs du job Spark
        while True:
            logs = subprocess.run(
                ["docker", "logs", "--tail", "10", "spark-master"],
                capture_output=True, text=True
            )
            logger.info("Derniers logs du job Spark:\n%s", logs.stdout)
            time.sleep(30)  # Vérifier les logs toutes les 30 secondes
    
    except subprocess.CalledProcessError as e:
        logger.error("Erreur lors du démarrage du job Spark: %s", e)
    except KeyboardInterrupt:
        logger.info("Arrêt du processus du job Spark")

def monitor_streamlit():
    """Surveille le dashboard Streamlit"""
    logger.info("Surveillance du dashboard Streamlit...")
    try:
        # Boucle pour surveiller les logs de Streamlit
        while True:
            logs = subprocess.run(
                ["docker", "logs", "--tail", "10", "streamlit"],
                capture_output=True, text=True
            )
            logger.info("Derniers logs du dashboard Streamlit:\n%s", logs.stdout)
            time.sleep(30)  # Vérifier les logs toutes les 30 secondes
    
    except subprocess.CalledProcessError as e:
        logger.error("Erreur lors de la surveillance du dashboard Streamlit: %s", e)
    except KeyboardInterrupt:
        logger.info("Arrêt de la surveillance du dashboard Streamlit")

def open_dashboard():
    """Ouvre le dashboard dans un navigateur"""
    import webbrowser
    logger.info("Ouverture du dashboard Streamlit dans le navigateur...")
    
    # Attendre que Streamlit soit prêt (60 secondes)
    time.sleep(60)
    
    # Ouvrir l'URL du dashboard
    url = "http://localhost:8501"
    webbrowser.open(url)
    logger.info(f"Dashboard ouvert à l'adresse {url}")

def main():
    """Fonction principale qui orchestre l'exécution du projet"""
    try:
        logger.info("Démarrage du projet d'analyse de sentiment en temps réel...")
        
        # Démarrer les services Docker
        if not start_docker_services():
            logger.error("Impossible de démarrer les services Docker. Arrêt du programme.")
            return
        
        # Créer les processus pour chaque composant
        producer_process = Process(target=start_tweet_producer)
        spark_process = Process(target=start_spark_job)
        streamlit_process = Process(target=monitor_streamlit)
        browser_process = Process(target=open_dashboard)
        
        # Démarrer les processus
        producer_process.start()
        logger.info("Attente de 10 secondes pour que le producteur démarre...")
        time.sleep(10)
        
        spark_process.start()
        logger.info("Attente de 20 secondes pour que le job Spark démarre...")
        time.sleep(20)
        
        streamlit_process.start()
        browser_process.start()
        
        # Afficher les URLs des interfaces
        logger.info("\nInterfaces disponibles:")
        logger.info("- Dashboard Streamlit: http://localhost:8501")
        logger.info("- Kibana: http://localhost:5601")
        logger.info("- Spark Master UI: http://localhost:8080")
        logger.info("- Elasticsearch: http://localhost:9200")
        
        logger.info("\nAppuyez sur Ctrl+C pour arrêter le projet...")
        
        # Attendre que les processus se terminent
        producer_process.join()
        spark_process.join()
        streamlit_process.join()
        browser_process.join()
        
    except KeyboardInterrupt:
        logger.info("\nArrêt du projet...")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du projet: {e}")
    finally:
        # Arrêter les services Docker
        logger.info("Arrêt des services Docker...")
        try:
            subprocess.run(["docker-compose", "down"], check=True)
            logger.info("Services Docker arrêtés avec succès")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'arrêt des services Docker: {e}")

if __name__ == "__main__":
    main() 