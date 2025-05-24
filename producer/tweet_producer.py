#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import random
import logging
from datetime import datetime
from faker import Faker
from kafka import KafkaProducer

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration du producteur Kafka
def create_producer():
    tries = 0
    max_tries = 10
    while tries < max_tries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=['kafka:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("Connexion établie avec succès au broker Kafka")
            return producer
        except Exception as e:
            tries += 1
            logger.warning(f"Tentative {tries}/{max_tries}: Impossible de se connecter à Kafka. Erreur: {e}")
            time.sleep(10)
    raise Exception("Impossible de se connecter au broker Kafka après plusieurs tentatives")

# Données pour la génération de tweets
HASHTAGS = ['#TradeWar', '#Tariffs', '#TradePolicy', '#GlobalTrade', '#EconomicPolicy', 
            '#TradeDispute', '#TradeAgreement', '#TradeTensions', '#TradeDeal']

POSITIVE_TEMPLATES = [
    "Les pourparlers commerciaux avec {country} progressent bien, {hashtag}. Perspectives optimistes!",
    "Après des mois de tensions, une avancée majeure dans les négociations commerciales avec {country}. {hashtag}",
    "Victoire pour notre économie! Un nouvel accord commercial avec {country} pourrait créer des milliers d'emplois. {hashtag}",
    "Les marchés en hausse suite à l'annonce d'une trêve dans les tensions commerciales avec {country}. {hashtag}",
    "Excellente nouvelle: une réduction des droits de douane sur les importations de {country} est en vue! {hashtag}",
    "Une nouvelle ère de coopération commerciale avec {country} vient de commencer. {hashtag}",
    "Accord commercial historique signé avec {country}, cela va dynamiser notre économie! {hashtag}",
    "Les entreprises célèbrent la fin des restrictions commerciales avec {country}. {hashtag}",
    "Les négociations commerciales s'avèrent prometteuses, les actions grimpent en flèche! {hashtag}",
    "Des signaux positifs émergent des négociations commerciales avec {country}. {hashtag}"
]

NEGATIVE_TEMPLATES = [
    "Les tensions commerciales avec {country} s'intensifient, sombre avenir pour nos exportations. {hashtag}",
    "Un nouveau cycle de tarifs douaniers imposés par {country} menace notre industrie. {hashtag}",
    "Les négociations commerciales avec {country} se sont effondrées, préparons-nous à des représailles. {hashtag}",
    "Inquiétudes croissantes face à l'impasse des pourparlers commerciaux avec {country}. {hashtag}",
    "Les marchés chutent alors que la guerre commerciale avec {country} s'intensifie. {hashtag}",
    "Alerte: {country} menace d'augmenter les droits de douane en réponse à nos mesures. {hashtag}",
    "Les entreprises souffrent des conséquences de la guerre commerciale avec {country}. {hashtag}",
    "Échec des négociations commerciales avec {country}, les tensions montent d'un cran. {hashtag}",
    "Impact dévastateur des nouvelles sanctions commerciales imposées par {country}. {hashtag}",
    "L'absence d'accord commercial avec {country} pourrait coûter des milliers d'emplois. {hashtag}"
]

NEUTRAL_TEMPLATES = [
    "Les négociations commerciales se poursuivent avec {country}, l'issue reste incertaine. {hashtag}",
    "Experts divisés sur l'impact potentiel des nouvelles politiques commerciales avec {country}. {hashtag}",
    "Analyse des implications de la situation commerciale actuelle avec {country}. {hashtag}",
    "Les marchés restent stables malgré les discussions commerciales en cours avec {country}. {hashtag}",
    "Réunion prévue pour discuter des relations commerciales avec {country}. {hashtag}",
    "Suivi des développements dans les négociations commerciales avec {country}. {hashtag}",
    "Débat sur l'équité des accords commerciaux actuels avec {country}. {hashtag}",
    "Les analystes évaluent l'impact des politiques commerciales sur nos relations avec {country}. {hashtag}",
    "Conférence internationale sur le commerce: {country} au centre des discussions. {hashtag}",
    "Publication d'un rapport sur l'état des échanges commerciaux avec {country}. {hashtag}"
]

COUNTRIES = [
    "la Chine", "les États-Unis", "l'UE", "le Canada", "le Mexique", 
    "le Japon", "la Corée du Sud", "l'Inde", "le Brésil", "l'Australie",
    "la Russie", "le Royaume-Uni", "l'Allemagne", "la France", "l'Italie"
]

# Fonction principale pour générer des tweets
def generate_tweet():
    fake = Faker()
    tweet_type = random.choices(["positive", "negative", "neutral"], weights=[0.3, 0.4, 0.3])[0]
    
    if tweet_type == "positive":
        template = random.choice(POSITIVE_TEMPLATES)
        sentiment = "positive"
    elif tweet_type == "negative":
        template = random.choice(NEGATIVE_TEMPLATES)
        sentiment = "negative"
    else:
        template = random.choice(NEUTRAL_TEMPLATES)
        sentiment = "neutral"
    
    country = random.choice(COUNTRIES)
    hashtags = random.sample(HASHTAGS, k=random.randint(1, 3))
    hashtag_text = " ".join(hashtags)
    
    tweet_text = template.format(country=country, hashtag=hashtag_text)
    
    tweet = {
        'id': fake.uuid4(),
        'user': fake.user_name(),
        'text': tweet_text,
        'hashtags': hashtags,
        'timestamp': datetime.now().isoformat(),
        'location': fake.city(),
        'true_sentiment': sentiment  # Pour validation
    }
    
    return tweet

def main():
    try:
        producer = create_producer()
        topic_name = 'twitter_stream'
        
        # Vérification si le topic existe, sinon il sera créé automatiquement
        logger.info(f"Préparation à l'envoi de tweets au topic Kafka: {topic_name}")
        
        tweet_count = 0
        
        # Boucle principale pour générer et envoyer des tweets
        while True:
            tweet = generate_tweet()
            producer.send(topic_name, value=tweet)
            tweet_count += 1
            
            if tweet_count % 10 == 0:
                logger.info(f"Nombre total de tweets envoyés: {tweet_count}")
            
            # Ajout d'un délai aléatoire pour simuler un flux réaliste
            time.sleep(random.uniform(0.5, 3.0))
            
    except KeyboardInterrupt:
        logger.info("Arrêt du producteur de tweets")
    except Exception as e:
        logger.error(f"Erreur: {e}")
    finally:
        if 'producer' in locals():
            producer.flush()
            producer.close()
            logger.info("Producteur Kafka fermé")

if __name__ == "__main__":
    main() 