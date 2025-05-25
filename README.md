# Analyse de Sentiment en Temps Réel - Projet Big Data

Ce projet implémente une application d'analyse de sentiment en temps réel sur des tweets simulés, axée sur les tensions commerciales mondiales et d'autres sujets d'actualité. Il utilise une architecture Big Data moderne pour collecter, analyser et visualiser les sentiments exprimés dans les tweets.

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

### Flux de Données et Architecture

L'application suit une architecture de traitement de flux (stream processing) avec les étapes suivantes :

1. **Génération des tweets** → 2. **Transport via Kafka** → 3. **Analyse avec Spark** → 4. **Stockage dans Elasticsearch** → 5. **Visualisation avec Streamlit/Kibana**

Cette architecture découplée permet une haute disponibilité et une scalabilité horizontale de chaque composant.

### Producteur de Tweets

Le producteur génère des tweets simulés avec différents sentiments (positifs, négatifs, neutres). Les tweets sont créés à partir de modèles prédéfinis et contiennent :

- Un identifiant unique (UUID)
- Un nom d'utilisateur fictif
- Le texte du tweet avec un sentiment prédéfini
- Des hashtags pertinents
- Un horodatage
- Une localisation fictive
- Le sentiment "réel" (pour validation)

**Exemples de tweets générés :**

```json
// Tweet positif
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": "trader_jane",
  "text": "Les pourparlers commerciaux avec la Chine progressent bien, #TradeWar #GlobalTrade. Perspectives optimistes!",
  "hashtags": ["#TradeWar", "#GlobalTrade"],
  "timestamp": "2025-05-25T13:28:36Z",
  "location": "New York",
  "true_sentiment": "positive"
}

// Tweet négatif
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "user": "market_analyst",
  "text": "Les tensions commerciales avec l'UE s'intensifient, sombre avenir pour nos exportations. #TradeDispute #Tariffs",
  "hashtags": ["#TradeDispute", "#Tariffs"],
  "timestamp": "2025-05-25T13:29:42Z",
  "location": "Chicago",
  "true_sentiment": "negative"
}
```

Les tweets sont générés à intervalles aléatoires (entre 0,5 et 3 secondes) pour simuler un flux réaliste.

### Analyse de Sentiment

L'analyse de sentiment est réalisée principalement avec VADER (Valence Aware Dictionary and sEntiment Reasoner), spécialement conçu pour les textes courts comme les tweets :

- **VADER** calcule un score de sentiment composé pour chaque tweet
- En fonction de ce score, le tweet est classé comme :
  - **Positif** : score ≥ 0.05
  - **Négatif** : score ≤ -0.05
  - **Neutre** : score entre -0.05 et 0.05

Le système peut également être configuré pour utiliser TextBlob comme alternative ou en complément de VADER.

**Métriques d'analyse :**

| Métrique | Description |
|----------|-------------|
| Compound Score | Score global entre -1 (très négatif) et +1 (très positif) |
| Positive Score | Intensité du sentiment positif (0 à 1) |
| Negative Score | Intensité du sentiment négatif (0 à 1) |
| Neutral Score | Intensité du sentiment neutre (0 à 1) |

### Stockage et Indexation

Elasticsearch stocke les tweets analysés dans l'index `twitter_sentiment` avec le mapping suivant :

```json
{
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
```

Cette structure permet des requêtes rapides et des agrégations complexes sur les données.

### Visualisation

Le dashboard Streamlit offre une visualisation interactive et actualisée des données, incluant :

- **Métriques principales** : Nombre total de tweets, pourcentage de tweets positifs et négatifs
- **Répartition des sentiments** : Graphique circulaire montrant la proportion de tweets positifs, négatifs et neutres
- **Évolution temporelle** : Graphique linéaire montrant l'évolution des sentiments au fil du temps
- **Hashtags populaires** : Graphique à barres des hashtags les plus fréquents
- **Tweets récents** : Tableau des 10 derniers tweets avec code couleur selon le sentiment

Le dashboard se rafraîchit automatiquement selon l'intervalle défini par l'utilisateur (par défaut toutes les 10 secondes).

## Résolution des problèmes courants

- **Erreur de connexion Kafka** : Assurez-vous que les services sont correctement démarrés `docker-compose ps`. Vérifiez les logs avec `docker logs kafka`.
- **Pas de données dans Elasticsearch** : Vérifiez les logs du consommateur Spark pour identifier les erreurs avec `docker logs spark-master`.
- **Problème avec Spark** : Vérifiez que le job Spark a bien été soumis et qu'il est en cours d'exécution via l'interface Spark Master UI (http://localhost:8080).
- **Dashboard Streamlit vide** : Assurez-vous qu'Elasticsearch contient des données et que le service Streamlit est en cours d'exécution.
- **Erreur de mémoire Docker** : Augmentez la mémoire allouée à Docker dans les paramètres de Docker Desktop.
- **Ports déjà utilisés** : Vérifiez si d'autres applications utilisent les ports requis et libérez-les si nécessaire.

## Personnalisation et Extension

### Modification des tweets générés

Vous pouvez personnaliser les tweets générés en modifiant les templates dans le fichier `producer/tweet_producer.py`. Les templates sont organisés par sentiment (positif, négatif, neutre) et peuvent être adaptés à différents sujets ou langues.

### Ajout de nouveaux modèles d'analyse de sentiment

Pour intégrer un nouveau modèle d'analyse de sentiment :

1. Ajoutez le code d'analyse dans `consumer/sentiment_analyzer.py`
2. Créez une nouvelle UDF (User Defined Function) pour le modèle
3. Modifiez le pipeline Spark pour utiliser cette nouvelle UDF

### Personnalisation du dashboard

Le dashboard Streamlit peut être facilement personnalisé en modifiant `visualization/dashboard.py`. Vous pouvez ajouter de nouvelles visualisations, modifier les existantes ou changer l'apparence générale.

### Extension vers d'autres sources de données

Le système peut être étendu pour analyser des tweets réels en remplaçant le producteur simulé par une connexion à l'API Twitter (maintenant X). Pour cela :

1. Créez un compte développeur sur Twitter/X
2. Obtenez les clés API nécessaires
3. Modifiez `producer/tweet_producer.py` pour utiliser l'API Twitter au lieu de générer des tweets simulés

## Performances et Optimisation

### Métriques de performance

Le système est conçu pour traiter plusieurs centaines de tweets par minute avec la configuration par défaut. Les performances peuvent être surveillées via :

- **Spark UI** : Métriques de traitement des données
- **Kafka Manager** (optionnel) : Surveillance des topics et des consommateurs
- **Elasticsearch Monitoring** : Utilisation des ressources et performance des requêtes

### Optimisation pour de grands volumes

Pour traiter de plus grands volumes de données :

1. Augmentez le nombre de partitions du topic Kafka
2. Ajoutez des workers Spark supplémentaires
3. Optimisez les paramètres Elasticsearch (shards, replicas)
4. Configurez un cluster Elasticsearch multi-nœuds

## Contribution au projet

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout de ma fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
- Personnalisez `visualization/dashboard.py` pour créer vos propres visualisations 