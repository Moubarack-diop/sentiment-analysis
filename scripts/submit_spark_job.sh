#!/bin/bash

# Script pour soumettre le job Spark d'analyse de sentiment

echo 'Soumission du job Spark...'
sleep 30
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 --conf spark.jars.ivy=/tmp/.ivy --conf spark.hadoop.hadoop.security.authentication=simple --conf spark.hadoop.hadoop.security.authorization=false /opt/bitnami/spark/consumer/sentiment_analyzer.py
echo 'Job soumis!'
