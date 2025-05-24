#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, from_json, to_json, struct
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, TimestampType
from textblob import TextBlob
from elasticsearch import Elasticsearch
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Définir la variable d'environnement HADOOP_USER_NAME pour résoudre le problème d'authentification
os.environ['HADOOP_USER_NAME'] = 'root'

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Fonction pour analyser le sentiment avec TextBlob
def analyze_sentiment_textblob(text):
    try:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1:
            return "positive"
        elif polarity < -0.1:
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de sentiment avec TextBlob: {e}")
        return "error"

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
                                "sentiment_textblob": {"type": "keyword"},
                                "sentiment_vader": {"type": "keyword"},
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
    
    # Définition des UDFs pour l'analyse de sentiment
    textblob_udf = udf(analyze_sentiment_textblob, StringType())
    vader_udf = udf(analyze_sentiment_vader, StringType())
    
    # Lecture du flux Kafka
    kafka_stream_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "twitter_stream") \
        .option("startingOffsets", "latest") \
        .load()
    
    # Parsing des données JSON depuis Kafka
    tweets_df = kafka_stream_df \
        .selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), tweet_schema).alias("tweet")) \
        .select("tweet.*")
    
    # Application des UDFs pour l'analyse de sentiment
    analyzed_tweets_df = tweets_df \
        .withColumn("sentiment_textblob", textblob_udf(col("text"))) \
        .withColumn("sentiment_vader", vader_udf(col("text")))
    
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
    
    # Attendre que les requêtes se terminent
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur dans l'application principale: {e}") 