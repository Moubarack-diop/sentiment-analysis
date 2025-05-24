# Analyse de Sentiment en Temps Réel - Projet Big Data

Ce projet implémente une application d'analyse de sentiment en temps réel sur des tweets simulés, axée sur les tensions commerciales mondiales.

## Architecture du Projet

![Architecture](https://miro.medium.com/max/1400/1*QUc1A1S12MX8LajQYLhvmg.png)

Le projet utilise les technologies suivantes :
- **Kafka** : Système de messagerie pour le flux de données en temps réel
- **Spark Structured Streaming** : Traitement du flux de données et analyse de sentiment
- **Elasticsearch** : Stockage et indexation des résultats
- **Kibana/Streamlit** : Visualisation des résultats d'analyse
- **Docker** : Conteneurisation de tous les services

## Structure du Projet

```
sentiment-analysis-project/
│
├── docker-compose.yml       # Configuration des services Docker
│
├── producer/                # Module de production de tweets simulés
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tweet_producer.py
│
├── consumer/                # Module d'analyse avec Spark
│   ├── Dockerfile
│   └── sentiment_analyzer.py
│
├── visualization/           # Interface de visualisation Streamlit
│   ├── Dockerfile
│   ├── requirements.txt
│   └── dashboard.py
│
├── config/                  # Fichiers de configuration
│
├── scripts/                 # Scripts utilitaires
│   └── submit_spark_job.sh
│
├── run_project.py           # Script d'automatisation Python
├── run_project.bat          # Script de lancement pour Windows
├── run_project.sh           # Script de lancement pour Linux/macOS
│
└── README.md                # Ce fichier
```

## Prérequis

- Windows 11 ou Linux/macOS
- Docker Desktop pour Windows / Docker et Docker Compose
- Python 3.8+
- Au moins 8GB de RAM disponible pour Docker
- Ports 9092, 2181, 9200, 5601, 8080, 8081 et 8501 disponibles

## Installation et Démarrage

### Méthode 1 : Lancement automatisé (recommandée)

Le projet inclut des scripts d'automatisation qui facilitent le démarrage de tous les composants.

#### Sous Windows:

```bash
# Double-cliquez simplement sur le fichier run_project.bat
# ou exécutez-le depuis une invite de commande
run_project.bat
```

#### Sous Linux/macOS:

```bash
# Rendez le script exécutable
chmod +x run_project.sh

# Lancez le script
./run_project.sh
```

Le script d'automatisation va:
1. Vérifier les prérequis (Python, Docker)
2. Installer les dépendances Python nécessaires
3. Démarrer tous les services Docker via docker-compose
4. Lancer le producteur de tweets
5. Lancer le job Spark pour l'analyse de sentiment
6. Surveiller le dashboard Streamlit
7. Ouvrir automatiquement le dashboard dans votre navigateur

Pour arrêter tous les services, appuyez simplement sur `Ctrl+C` dans la fenêtre de commande.

### Méthode 2 : Lancement manuel (pour les utilisateurs avancés)

1. **Clonez ce projet**

```bash
git clone <url-du-repo>
cd sentiment-analysis-project
```

2. **Lancez les services avec Docker Compose**

```bash
docker-compose up -d
```

Ce processus va :
- Télécharger toutes les images Docker nécessaires
- Créer les conteneurs pour Kafka, Zookeeper, Spark, Elasticsearch, Kibana, etc.
- Configurer les réseaux et volumes nécessaires

3. **Attendre que tous les services démarrent**

Attendez environ 1-2 minutes que tous les services soient correctement initialisés. Vous pouvez vérifier l'état des conteneurs avec :

```bash
docker-compose ps
```

4. **Démarrer le producteur de tweets**

Le producteur de tweets démarre automatiquement, mais vous pouvez vérifier ses logs avec :

```bash
docker logs python-producer
```

5. **Lancer le job Spark pour analyser les tweets**

Pour démarrer l'analyse de sentiment avec Spark Structured Streaming :

```bash
# Sous Linux/macOS
chmod +x scripts/submit_spark_job.sh
./scripts/submit_spark_job.sh

# Sous Windows
docker exec -it spark-master /opt/bitnami/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 --conf "spark.jars.ivy=/tmp/.ivy" /opt/bitnami/spark/consumer/sentiment_analyzer.py
```

6. **Accéder aux interfaces de visualisation**

- **Streamlit** : http://localhost:8501
- **Kibana** : http://localhost:5601
- **Spark Master UI** : http://localhost:8080

## Configuration de Kibana (optionnel)

Si vous souhaitez utiliser Kibana pour visualiser les données :

1. Accédez à Kibana via http://localhost:5601
2. Allez dans Management > Stack Management > Index Patterns
3. Créez un nouvel index pattern avec `twitter_sentiment*`
4. Sélectionnez `timestamp` comme champ de temps
5. Créez ensuite vos propres visualisations et dashboards

## Arrêt du Projet

### En utilisant le script automatisé

Si vous utilisez le script automatisé (`run_project.py`), appuyez simplement sur `Ctrl+C` dans la console. Le script s'occupera d'arrêter proprement tous les services.

### En manuel

Pour arrêter tous les services :

```bash
docker-compose down
```

Pour supprimer également les volumes (données persistantes) :

```bash
docker-compose down -v
```

## Détails Techniques

### Producteur de Tweets

Le producteur génère des tweets simulés concernant les tensions commerciales entre différents pays, avec différents sentiments (positifs, négatifs, neutres). Les tweets contiennent des hashtags comme #TradeWar, #Tariffs, etc.

### Analyse de Sentiment

L'analyse de sentiment est réalisée à l'aide de deux approches :
1. **TextBlob** : Bibliothèque Python simple pour le traitement du langage naturel
2. **VADER** (Valence Aware Dictionary and sEntiment Reasoner) : Spécialement adapté pour les textes courts comme les tweets

### Visualisation

Le dashboard Streamlit permet de :
- Visualiser la répartition des sentiments
- Suivre l'évolution des sentiments au fil du temps
- Identifier les hashtags les plus fréquents
- Examiner les tweets récents avec leur sentiment associé

## Résolution des problèmes courants

- **Erreur de connexion Kafka** : Assurez-vous que les services sont correctement démarrés `docker-compose ps`
- **Pas de données dans Elasticsearch** : Vérifiez les logs du consommateur Spark pour identifier les erreurs
- **Problème avec Spark** : Vérifiez que le job Spark a bien été soumis et qu'il est en cours d'exécution
- **Script d'automatisation qui échoue** : Vérifiez que tous les prérequis sont installés (Python, Docker)

## Personnalisation

- Modifiez `producer/tweet_producer.py` pour changer le type de tweets générés
- Adaptez `consumer/sentiment_analyzer.py` pour modifier l'analyse ou ajouter d'autres méthodes
- Personnalisez `visualization/dashboard.py` pour créer vos propres visualisations 