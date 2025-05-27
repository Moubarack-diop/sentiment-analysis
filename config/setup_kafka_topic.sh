#!/bin/bash

# Script pour configurer le topic Kafka avec les bonnes propriétés
# Ce script doit être exécuté après le démarrage des conteneurs Kafka

echo "Configuration du topic Kafka pour l'analyse de sentiment..."

# Attendre que Kafka soit prêt
echo "Attente du démarrage de Kafka..."
sleep 30

# Appliquer les optimisations de configuration
echo "Application des optimisations de configuration..."
if [ -f "/scripts/kafka_optimizations.properties" ]; then
  # Copier les configurations dans les brokers (simulation - dans un environnement réel, cela nécessiterait un redémarrage)
  echo "Fichier de configuration trouvé. Dans un environnement de production, ces paramètres seraient appliqués directement aux brokers."
  cat /scripts/kafka_optimizations.properties
else
  echo "Fichier de configuration non trouvé. Utilisation des paramètres par défaut."
fi

# Créer le topic avec 3 partitions et un facteur de réplication de 2
kafka-topics.sh --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 2 \
  --partitions 3 \
  --topic twitter_stream \
  --if-not-exists \
  --config retention.ms=604800000 \
  --config retention.bytes=1073741824 \
  --config segment.bytes=268435456 \
  --config segment.ms=3600000 \
  --config min.insync.replicas=1 \
  --config cleanup.policy=delete \
  --config flush.messages=10000 \
  --config flush.ms=60000 \
  --config unclean.leader.election.enable=false

# Vérifier que le topic a été créé correctement
echo "Vérification de la configuration du topic..."
kafka-topics.sh --describe --bootstrap-server kafka:9092 --topic twitter_stream

# Créer les répertoires de checkpoints pour Spark
echo "Création des répertoires de checkpoints pour Spark..."
mkdir -p /opt/bitnami/spark/checkpoints/elasticsearch
mkdir -p /opt/bitnami/spark/checkpoints/alerts

echo "Configuration terminée!"
