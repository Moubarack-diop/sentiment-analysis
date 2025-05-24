#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time

# URL de l'API Elasticsearch
ELASTICSEARCH_URL = "http://localhost:9200"

# Données de test
test_data = {
    "id": "test123",
    "user": "testuser",
    "text": "This is a test tweet! I love this project. #python #datascience",
    "hashtags": ["python", "datascience"],
    "timestamp": "2025-05-24T20:00:00",
    "location": "test",
    "sentiment": "positive",
    "true_sentiment": "positive"
}

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

time.sleep(2)

# Insérer le document de test
print("Insertion du document de test...")
try:
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{ELASTICSEARCH_URL}/twitter_sentiment/_doc/test123",
        headers=headers,
        data=json.dumps(test_data)
    )
    print(f"Insertion du document test réponse: {response.status_code}, {response.text}")
except Exception as e:
    print(f"Erreur lors de l'insertion du document test: {e}")

# Insérer quelques documents supplémentaires avec différents sentiments
for i in range(1, 5):
    sentiment = "positive" if i % 3 == 0 else "negative" if i % 3 == 1 else "neutral"
    doc = {
        "id": f"test{i}",
        "user": f"user{i}",
        "text": f"Test tweet number {i} with {sentiment} sentiment",
        "hashtags": ["test"],
        "timestamp": f"2025-05-24T{19+i}:00:00",
        "location": "test",
        "sentiment": sentiment,
        "true_sentiment": sentiment
    }
    print(f"Insertion du document {i}...")
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{ELASTICSEARCH_URL}/twitter_sentiment/_doc/test{i}",
            headers=headers,
            data=json.dumps(doc)
        )
        print(f"Insertion du document {i} réponse: {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de l'insertion du document {i}: {e}")

# Rafraîchir l'index
print("Rafraîchissement de l'index...")
try:
    response = requests.post(f"{ELASTICSEARCH_URL}/twitter_sentiment/_refresh")
    print(f"Rafraîchissement réponse: {response.status_code}")
except Exception as e:
    print(f"Erreur lors du rafraîchissement de l'index: {e}")

print("Terminé. Vérifiez le dashboard Streamlit à l'adresse http://localhost:8501") 