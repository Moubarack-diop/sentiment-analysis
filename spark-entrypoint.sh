#!/bin/bash

# Installer les dépendances nécessaires
pip install elasticsearch==7.17.0 nltk kafka-python
python -m nltk.downloader vader_lexicon

# Démarrer le service Spark
/opt/bitnami/scripts/spark/entrypoint.sh /opt/bitnami/scripts/spark/run.sh &

# Attendre que le service Spark soit démarré
echo "Attente de 30 secondes pour que le service Spark démarre..."
sleep 30

# Vérifier que le service Spark est bien démarré
if ! pgrep -f "org.apache.spark.deploy.master.Master" > /dev/null; then
    echo "Le service Spark Master n'a pas démarré correctement."
    exit 1
fi

echo "Service Spark démarré avec succès. Lancement du job d'analyse de sentiment..."

# Lancer le job d'analyse de sentiment avec des options de mémoire réduites
/opt/bitnami/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  --conf spark.jars.ivy=/tmp/.ivy \
  --conf spark.driver.memory=512m \
  --conf spark.executor.memory=512m \
  --conf spark.memory.fraction=0.6 \
  --conf spark.memory.storageFraction=0.2 \
  /opt/bitnami/spark/consumer/sentiment_analyzer.py 