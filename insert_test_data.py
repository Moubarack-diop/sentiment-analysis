#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import json
import time

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
subprocess.run([
    "docker", "exec", "-it", "elasticsearch", 
    "curl", "-X", "DELETE", "localhost:9200/twitter_sentiment"
])

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

# Enregistrer le mapping dans un fichier temporaire
with open("mapping.json", "w") as f:
    json.dump(mapping, f)

# Créer l'index avec le mapping via docker exec
subprocess.run([
    "docker", "exec", "-it", "elasticsearch",
    "curl", "-X", "PUT", "localhost:9200/twitter_sentiment", 
    "-H", "Content-Type: application/json", 
    "-d", json.dumps(mapping)
])

print("Index créé")
time.sleep(2)

# Insérer le document de test
print("Insertion du document de test...")
subprocess.run([
    "docker", "exec", "-it", "elasticsearch",
    "curl", "-X", "POST", "localhost:9200/twitter_sentiment/_doc/test123", 
    "-H", "Content-Type: application/json", 
    "-d", json.dumps(test_data)
])

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
    subprocess.run([
        "docker", "exec", "-it", "elasticsearch",
        "curl", "-X", "POST", f"localhost:9200/twitter_sentiment/_doc/test{i}", 
        "-H", "Content-Type: application/json", 
        "-d", json.dumps(doc)
    ])

# Rafraîchir l'index
print("Rafraîchissement de l'index...")
subprocess.run([
    "docker", "exec", "-it", "elasticsearch",
    "curl", "-X", "POST", "localhost:9200/twitter_sentiment/_refresh"
])

print("Terminé. Vérifiez le dashboard Streamlit à l'adresse http://localhost:8501") 