#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, from_json, to_json, struct, window, count, when, sum, expr
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, TimestampType, BooleanType
from elasticsearch import Elasticsearch
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime

# Définir la variable d'environnement HADOOP_USER_NAME pour résoudre le problème d'authentification
os.environ['HADOOP_USER_NAME'] = 'root'

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration des seuils d'alerte
NEGATIVE_THRESHOLD = 0.60  # Alerte si plus de 60% des tweets sont négatifs
POSITIVE_THRESHOLD = 0.80  # Alerte si plus de 80% des tweets sont positifs
WINDOW_DURATION = "5 minutes"  # Fenêtre d'analyse
SLIDE_DURATION = "1 minute"    # Fréquence d'analyse

# Téléchargement des ressources NLTK pour l'analyse de sentiment
try:
    nltk.download('vader_lexicon')
except Exception as e:
    logger.warning(f"Erreur lors du téléchargement de vader_lexicon: {e}")

# Schéma des tweets entrants
tweet_schema = StructType([
    StructField("id", StringType(), True),
    StructField("user", StringType(), True),
    StructField("text", StringType(), True),
    StructField("hashtags", ArrayType(StringType()), True),
    StructField("timestamp", StringType(), True),
    StructField("location", StringType(), True),
    StructField("true_sentiment", StringType(), True)
])

# Fonction pour analyser le sentiment avec VADER
def analyze_sentiment_vader(text):
    try:
        sid = SentimentIntensityAnalyzer()
        sentiment_score = sid.polarity_scores(text)
        compound_score = sentiment_score['compound']
        
        if compound_score >= 0.05:
            return "positive"
        elif compound_score <= -0.05:
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de sentiment avec VADER: {e}")
        return "error"

# Tentative de connexion à Elasticsearch avec plusieurs essais
def connect_to_elasticsearch():
    es = None
    retry_count = 0
    max_retries = 10
    
    while es is None and retry_count < max_retries:
        try:
            es = Elasticsearch(['http://elasticsearch:9200'])
            if es.ping():
                logger.info("Connexion à Elasticsearch réussie")
                # Création de l'index s'il n'existe pas déjà
                if not es.indices.exists(index="twitter_sentiment"):
                    mapping = {
                        "mappings": {
                            "properties": {
                                "id": {"type": "keyword"},
                                "user": {"type": "keyword"},
                                "text": {"type": "text"},
                                "hashtags": {"type": "keyword"},
                                "timestamp": {"type": "date"},
                                "location": {"type": "keyword"},
                                "sentiment": {"type": "keyword"},
                                "true_sentiment": {"type": "keyword"}
                            }
                        }
                    }
                    es.indices.create(index="twitter_sentiment", body=mapping)
                    logger.info("Index twitter_sentiment créé avec succès")
                return es
            else:
                logger.warning("Impossible de ping Elasticsearch")
        except Exception as e:
            logger.warning(f"Tentative {retry_count+1}/{max_retries}: Erreur de connexion à Elasticsearch: {e}")
            retry_count += 1
            time.sleep(10)
    
    if es is None:
        logger.error("Impossible de se connecter à Elasticsearch après plusieurs tentatives")
    return es

# Fonction pour envoyer les données à Elasticsearch
def send_to_elasticsearch(tweet_batch_df, batch_id):
    es = connect_to_elasticsearch()
    if es is None:
        logger.error("Elasticsearch indisponible, les données ne seront pas envoyées")
        return
    
    tweets = tweet_batch_df.collect()
    for tweet in tweets:
        try:
            tweet_dict = tweet.asDict()
            es.index(index="twitter_sentiment", id=tweet_dict["id"], body=tweet_dict)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données à Elasticsearch: {e}")

# Fonction pour vérifier les seuils et déclencher des alertes
def check_sentiment_thresholds(batch_df, batch_id):
    try:
        # Compter les tweets par sentiment
        sentiment_counts = batch_df.groupBy("sentiment").count().collect()
        
        # Convertir en dictionnaire pour faciliter l'accès
        counts = {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
        for row in sentiment_counts:
            sentiment = row["sentiment"]
            count = row["count"]
            counts[sentiment] = count
            counts["total"] += count
        
        if counts["total"] > 0:
            # Calculer les pourcentages
            negative_pct = (counts["negative"] / counts["total"]) * 100
            positive_pct = (counts["positive"] / counts["total"]) * 100
            
            # Créer un dictionnaire pour stocker les informations d'alerte
            alert_info = {
                "timestamp": datetime.now().isoformat(),
                "negative_count": counts["negative"],
                "positive_count": counts["positive"],
                "neutral_count": counts["neutral"],
                "total_count": counts["total"],
                "negative_pct": negative_pct,
                "positive_pct": positive_pct,
                "negative_alert": False,
                "positive_alert": False
            }
            
            # Vérifier les seuils
            if negative_pct >= NEGATIVE_THRESHOLD * 100:
                logger.warning(f"ALERTE: {negative_pct:.2f}% des tweets sont négatifs!")
                alert_info["negative_alert"] = True
            
            if positive_pct >= POSITIVE_THRESHOLD * 100:
                logger.warning(f"ALERTE: {positive_pct:.2f}% des tweets sont positifs!")
                alert_info["positive_alert"] = True
            
            # Si une alerte est déclenchée, stocker l'information dans Elasticsearch
            if alert_info["negative_alert"] or alert_info["positive_alert"]:
                es = connect_to_elasticsearch()
                if es is not None:
                    es.index(index="sentiment_alerts", body=alert_info)
                    logger.info(f"Alerte enregistrée dans Elasticsearch")
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des seuils: {e}")

# Fonction pour créer l'index d'alertes s'il n'existe pas
def create_alerts_index():
    es = connect_to_elasticsearch()
    if es is None:
        logger.error("Elasticsearch indisponible, impossible de créer l'index d'alertes")
        return
    
    try:
        if not es.indices.exists(index="sentiment_alerts"):
            mapping = {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "negative_count": {"type": "integer"},
                        "positive_count": {"type": "integer"},
                        "neutral_count": {"type": "integer"},
                        "total_count": {"type": "integer"},
                        "negative_pct": {"type": "float"},
                        "positive_pct": {"type": "float"},
                        "negative_alert": {"type": "boolean"},
                        "positive_alert": {"type": "boolean"}
                    }
                }
            }
            es.indices.create(index="sentiment_alerts", body=mapping)
            logger.info("Index sentiment_alerts créé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'index d'alertes: {e}")

# Attendre que Kafka soit prêt
def wait_for_kafka():
    logger.info("En attente de Kafka...")
    time.sleep(30)  # Attendre 30 secondes pour s'assurer que Kafka est prêt

def main():
    # Attendre que les services soient prêts
    wait_for_kafka()
    
    # Création de la session Spark
    spark = SparkSession.builder \
        .appName("TwitterSentimentAnalysis") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1") \
        .config("spark.hadoop.hadoop.security.authentication", "simple") \
        .config("spark.hadoop.hadoop.security.authorization", "false") \
        .config("spark.hadoop.fs.defaultFS", "file:///") \
        .getOrCreate()
    
    # Réduction du niveau de log pour éviter trop de messages
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info("Session Spark créée, début du streaming...")
    
    # Créer l'index d'alertes dans Elasticsearch
    create_alerts_index()
    
    # Définition de l'UDF pour l'analyse de sentiment
    vader_udf = udf(analyze_sentiment_vader, StringType())
    
    # Lecture du flux Kafka
    kafka_stream_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "twitter_stream") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parsing des données JSON depuis Kafka
    tweets_df = kafka_stream_df \
        .selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), tweet_schema).alias("tweet")) \
        .select("tweet.*")
    
    # Application de l'UDF pour l'analyse de sentiment
    analyzed_tweets_df = tweets_df \
        .withColumn("sentiment", vader_udf(col("text")))
    
    # Affichage des résultats dans la console
    console_query = analyzed_tweets_df \
        .writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", False) \
        .start()
    
    # Envoi des résultats à Elasticsearch
    elasticsearch_query = analyzed_tweets_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(send_to_elasticsearch) \
        .start()
    
    # Analyse par fenêtre temporelle pour les alertes
    windowed_counts = analyzed_tweets_df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy(
            window(col("timestamp"), WINDOW_DURATION, SLIDE_DURATION),
            col("sentiment")
        ) \
        .count()
    
    # Requête pour déclencher les alertes
    alert_query = analyzed_tweets_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(check_sentiment_thresholds) \
        .start()
    
    # Attendre que les requêtes se terminent
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur dans l'application principale: {e}") 