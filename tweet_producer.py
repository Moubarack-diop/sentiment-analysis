#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time
import uuid
import random
from datetime import datetime

# Configuration globale - Modifiez ces valeurs selon vos besoins
ELASTICSEARCH_URL = "http://localhost:9200"
NUM_TWEETS = 1000000           # Nombre de tweets à générer
INTERVAL_MIN = 0.01        # Intervalle minimum entre les tweets (secondes)
INTERVAL_MAX = 0.1         # Intervalle maximum entre les tweets (secondes)
RESET_INDEX = True        # Si True, réinitialise l'index avant de commencer

# Fonction pour générer un tweet aléatoire
def create_random_tweet():
    # Sentiments possibles
    sentiments = ["positive", "negative", "neutral"]
    
    # Textes de tweets par sentiment
    tweet_texts = {
        "positive": [
            "I absolutely love this new product! It's amazing! #happy #satisfied",
            "Just had the best experience with customer service. They were so helpful! #greatservice",
            "The market is showing strong signs of recovery. Investors are optimistic. #finance #growth",
            "Our team won the championship! So proud of everyone's hard work. #victory #celebration",
            "This new technology is revolutionary and will change the industry forever. #innovation",
            "Absolutely loving the new AI tool at work. It's boosting my productivity! #AI #worklife",
        "My trip to Bali was magical. Such kind people and beautiful places! #travel",
        "The new vaccine rollout has been smooth and efficient. #health #progress",
        "Got promoted today! Hard work pays off. #career #success",
        "That movie had the perfect ending. Just what I needed. #cinema",
        "Our climate policy is finally making a difference. #green #hope",
        "Streaming my favorite song and feeling grateful. #music #goodvibes",
        "My son just graduated! So proud of him. #education #family",
        "That restaurant deserves a Michelin star. Incredible flavors! #foodie",
        "Finally got my dream job at Google. Hard work and patience! #careergoals"
        ],
        "negative": [
            "This product is terrible. Complete waste of money. #disappointed #angry",
            "The customer service was awful. I waited for hours and no one helped me. #badservice",
            "The market is crashing. Investors are panicking. #finance #recession",
            "Our team lost badly. Very disappointing performance. #defeat #sadness",
            "This technology is outdated and useless. #failure #waste",
             "This update just ruined the whole app experience. #fail",
        "I can't believe how poor the hospital service was. #healthcare #frustration",
        "The pollution in the city is unbearable. #climatecrisis",
        "Lost all my crypto savings. The market is brutal. #crypto #loss",
        "This movie was a total waste of time. #disappointed",
        "Still waiting for the technician who was supposed to come 3 hours ago. #badservice",
        "The education system is falling apart. Teachers are overwhelmed. #education",
        "Received expired food from delivery. Disgusting. #food",
        "The political debate was full of lies and manipulation. #politics #corruption",
        "That concert was a mess. Terrible sound and disorganization. #eventfail"
        
        ],
        "neutral": [
            "The product works as expected. Nothing special. #review",
            "Customer service responded to my inquiry. #service",
            "The market remained stable today. #finance #news",
            "The game ended in a draw. #sports #results",
            "This technology has both advantages and disadvantages. #analysis",
            "Attended a seminar on AI ethics today. Interesting perspectives. #tech",
        "Weather is mild and cloudy. #dailyupdate",
        "Just installed the latest OS update. Seems stable so far. #software",
        "Reading a book on behavioral economics. Quite insightful. #learning",
        "Visited the new mall in town. Pretty average experience. #citylife",
        "Conference starts at 9AM tomorrow. #event",
        "Watching a documentary on wildlife. Informative. #nature",
        "Tried the new food delivery app. Works like others. #review",
        "The currency exchange rate remained unchanged today. #finance",
        "Board meeting lasted 2 hours. Some useful discussions. #corporate"
        ]
    }
    
    # Hashtags communs
    common_hashtags = [
        "technology", "business", "finance", "market", "economy", 
        "trade", "global", "innovation", "policy", "development"
    ]
    
    # Noms d'utilisateurs
    usernames = ["trader_joe", "market_analyst", "tech_investor", "finance_guru", 
                  "economic_news", "business_insider", "global_trader", "policy_watcher"]
    
    # Locations
    locations = ["New York", "London", "Tokyo", "Singapore", "Hong Kong", 
                 "Frankfurt", "Paris", "Sydney", "Dubai", "Shanghai"]
    
    # Choisir un sentiment aléatoire
    sentiment = random.choice(sentiments)
    
    # Choisir un tweet correspondant au sentiment
    tweet_text = random.choice(tweet_texts[sentiment])
    
    # Extraire les hashtags existants
    existing_hashtags = []
    for word in tweet_text.split():
        if word.startswith("#"):
            existing_hashtags.append(word[1:])
    
    # Ajouter quelques hashtags aléatoires
    additional_hashtags = random.sample(common_hashtags, random.randint(1, 3))
    all_hashtags = existing_hashtags + additional_hashtags
    
    # Créer le tweet
    tweet = {
        "id": str(uuid.uuid4()),
        "user": random.choice(usernames),
        "text": tweet_text,
        "hashtags": all_hashtags,
        "timestamp": datetime.now().isoformat(),
        "location": random.choice(locations),
        "sentiment": sentiment,
        "true_sentiment": sentiment
    }
    
    return tweet

def setup_elasticsearch():
    """Configure l'index Elasticsearch pour les tweets"""
    # Supprimer l'index s'il existe
    print("Suppression de l'index s'il existe...")
    try:
        response = requests.delete(f"{ELASTICSEARCH_URL}/twitter_sentiment")
        print(f"Suppression réponse: {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de la suppression de l'index: {e}")

    # Attendre un peu
    time.sleep(2)

    # Créer l'index avec le mapping approprié
    print("Création de l'index avec le mapping...")
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

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.put(
            f"{ELASTICSEARCH_URL}/twitter_sentiment",
            headers=headers,
            data=json.dumps(mapping)
        )
        print(f"Création de l'index réponse: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Erreur lors de la création de l'index: {e}")

def insert_tweet(tweet):
    """Insère un tweet dans Elasticsearch"""
    tweet_id = tweet["id"]
    
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{ELASTICSEARCH_URL}/twitter_sentiment/_doc/{tweet_id}",
            headers=headers,
            data=json.dumps(tweet)
        )
        return response.status_code
    except Exception as e:
        print(f"Erreur lors de l'insertion du tweet: {e}")
        return None

def refresh_index():
    """Rafraîchit l'index Elasticsearch"""
    try:
        response = requests.post(f"{ELASTICSEARCH_URL}/twitter_sentiment/_refresh")
        print(f"Rafraîchissement réponse: {response.status_code}")
    except Exception as e:
        print(f"Erreur lors du rafraîchissement de l'index: {e}")

def generate_tweets():
    """
    Génère et envoie des tweets à Elasticsearch selon la configuration globale
    """
    # Initialiser l'index si nécessaire
    if RESET_INDEX:
        setup_elasticsearch()
    
    # Générer et envoyer les tweets
    print(f"\nGénération de {NUM_TWEETS} tweets...")
    count_success = 0
    
    try:
        for i in range(NUM_TWEETS):
            tweet = create_random_tweet()
            status = insert_tweet(tweet)
            
            sentiment = tweet["sentiment"]
            print(f"Tweet {i+1}/{NUM_TWEETS}: {tweet['text'][:50]}... [Sentiment: {sentiment}] - Status: {status}")
            
            if status == 201:
                count_success += 1
            
            # Rafraîchir l'index tous les 10 tweets
            if (i+1) % 10 == 0:
                refresh_index()
            
            # Attendre un intervalle aléatoire pour simuler le temps réel
            if i < NUM_TWEETS - 1 and (INTERVAL_MIN > 0 or INTERVAL_MAX > 0):
                delay = random.uniform(INTERVAL_MIN, INTERVAL_MAX)
                time.sleep(delay)
    
    except KeyboardInterrupt:
        print("\nGénération interrompue par l'utilisateur")
    
    finally:
        # Rafraîchir l'index à la fin
        refresh_index()
    
    print(f"\nTerminé. {count_success}/{NUM_TWEETS} tweets ont été envoyés avec succès.")
    print("Vérifiez le dashboard Streamlit à l'adresse http://localhost:8501")

if __name__ == "__main__":
    generate_tweets() 