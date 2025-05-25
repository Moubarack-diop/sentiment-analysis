#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fonction pour se connecter à Elasticsearch
def connect_to_elasticsearch():
    try:
        es = Elasticsearch(['http://elasticsearch:9200'])
        if es.ping():
            logger.info("Connexion à Elasticsearch réussie")
            return es
        else:
            logger.warning("Impossible de ping Elasticsearch")
            return None
    except Exception as e:
        logger.error(f"Erreur de connexion à Elasticsearch: {e}")
        return None

# Fonction pour récupérer les données depuis Elasticsearch
def get_data_from_elasticsearch(es, time_range_minutes=30):
    try:
        # Requête pour récupérer tous les tweets sans filtrage par date
        query = {
            "size": 5000,  # Limite à 1000 résultats
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "match_all": {}  # Récupérer tous les documents
            }
        }
        
        response = es.search(index="twitter_sentiment", body=query)
        
        # Transformer les résultats en DataFrame
        hits = response['hits']['hits']
        data = [hit['_source'] for hit in hits]
        
        if data:
            df = pd.DataFrame(data)
            return df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données depuis Elasticsearch: {e}")
        return pd.DataFrame()

# Fonction pour récupérer les alertes depuis Elasticsearch
def get_alerts_from_elasticsearch(es, time_range_minutes=30):
    try:
        # Calculer la date limite pour la fenêtre d'analyse
        time_limit = datetime.now() - timedelta(minutes=time_range_minutes)
        time_limit_str = time_limit.isoformat()
        
        # Requête pour récupérer les alertes récentes
        query = {
            "size": 100,  # Limite à 100 alertes
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": time_limit_str
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"term": {"negative_alert": True}},
                                    {"term": {"positive_alert": True}}
                                ]
                            }
                        }
                    ]
                }
            }
        }
        
        # Vérifier si l'index existe avant de faire la requête
        if es.indices.exists(index="sentiment_alerts"):
            response = es.search(index="sentiment_alerts", body=query)
            
            # Transformer les résultats en DataFrame
            hits = response['hits']['hits']
            data = [hit['_source'] for hit in hits]
            
            if data:
                df = pd.DataFrame(data)
                return df
        
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des alertes depuis Elasticsearch: {e}")
        return pd.DataFrame()

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Analyse de Sentiment en Temps Réel",
    page_icon="📊",
    layout="wide"
)

# Titre de l'application
st.title("📊 Analyse de Sentiment en Temps Réel - Tweets sur les Tensions Commerciales")

# Sidebar pour les options
st.sidebar.header("Options")
refresh_interval = st.sidebar.slider("Intervalle de rafraîchissement (secondes)", 5, 60, 10)
time_range = st.sidebar.slider("Période d'analyse (minutes)", 5, 120, 30)

# Configuration des seuils d'alerte (avec possibilité de les ajuster)
st.sidebar.header("Configuration des alertes")
show_alerts = st.sidebar.checkbox("Afficher les alertes", value=True)
negative_threshold = st.sidebar.slider("Seuil d'alerte négative (%)", 30, 90, 60)
positive_threshold = st.sidebar.slider("Seuil d'alerte positive (%)", 30, 90, 80)

# Connexion à Elasticsearch
es = connect_to_elasticsearch()

if es is None:
    st.error("❌ Impossible de se connecter à Elasticsearch. Vérifiez que le service est en cours d'exécution.")
else:
    st.success("✅ Connecté à Elasticsearch")

    # Fonction principale pour mettre à jour le tableau de bord
    def update_dashboard():
        # Récupération des données
        df = get_data_from_elasticsearch(es, time_range)
        
        if df.empty:
            st.warning("Aucune donnée disponible pour la période sélectionnée.")
            return
        
        # Récupération des alertes si activées
        if show_alerts:
            alerts_df = get_alerts_from_elasticsearch(es, time_range)
        
        # Préparation des données
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        except Exception as e:
            st.error(f"Erreur lors du traitement des données: {e}")
            return
        
        # Affichage des métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nombre de tweets analysés", len(df))
        
        # Utiliser la colonne 'sentiment'
        sentiment_col = "sentiment"
        
        # Afficher les métriques
        with col2:
            positive_pct = round(100 * df[df[sentiment_col] == 'positive'].shape[0] / len(df), 1)
            st.metric("Tweets positifs", f"{positive_pct}%")
        
        with col3:
            negative_pct = round(100 * df[df[sentiment_col] == 'negative'].shape[0] / len(df), 1)
            st.metric("Tweets négatifs", f"{negative_pct}%")
        
        # Graphique de répartition des sentiments
        st.subheader("Répartition des sentiments")
        
        sentiment_counts = df[sentiment_col].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        fig = px.pie(sentiment_counts, values='Count', names='Sentiment', 
                     title='Répartition des sentiments',
                     color_discrete_map={'positive':'green', 'neutral':'gray', 'negative':'red'})
        st.plotly_chart(fig)
        
        # Évolution des sentiments au fil du temps
        st.subheader("Évolution des sentiments au fil du temps")
        
        # Regrouper par intervalle de temps (5 minutes)
        df['time_bucket'] = df['timestamp'].dt.floor('5min')
        
        sentiment_over_time = df.groupby(['time_bucket', sentiment_col]).size().unstack(fill_value=0)
        
        fig = go.Figure()
        
        if 'positive' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(x=sentiment_over_time.index, y=sentiment_over_time['positive'],
                                    mode='lines+markers', name='Positif', line=dict(color='green')))
        if 'neutral' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(x=sentiment_over_time.index, y=sentiment_over_time['neutral'],
                                    mode='lines+markers', name='Neutre', line=dict(color='gray')))
        if 'negative' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(x=sentiment_over_time.index, y=sentiment_over_time['negative'],
                                    mode='lines+markers', name='Négatif', line=dict(color='red')))
        
        fig.update_layout(title=f'Évolution des sentiments au fil du temps',
                         xaxis_title='Temps', yaxis_title='Nombre de tweets')
        st.plotly_chart(fig)
        
        # Hashtags les plus fréquents
        st.subheader("Hashtags les plus fréquents")
        
        # Extraire tous les hashtags
        all_hashtags = []
        for hashtags in df['hashtags']:
            if hashtags:
                all_hashtags.extend(hashtags)
        
        if all_hashtags:
            hashtag_counts = pd.Series(all_hashtags).value_counts().reset_index()
            hashtag_counts.columns = ['Hashtag', 'Count']
            hashtag_counts = hashtag_counts.head(10)  # Top 10
            
            fig = px.bar(hashtag_counts, x='Hashtag', y='Count', title='Top 10 des hashtags')
            st.plotly_chart(fig)
        else:
            st.info("Aucun hashtag trouvé dans les données")
        
        # Section d'alertes de sentiment
        if show_alerts:
            st.subheader("Système d'alertes de sentiment")
            
            # Vérification des seuils sur les données récentes
            recent_data = df[df['timestamp'] > (datetime.now() - timedelta(minutes=30))]
            
            if not recent_data.empty:
                # Calculer les pourcentages
                total_tweets = len(recent_data)
                positive_count = len(recent_data[recent_data[sentiment_col] == 'positive'])
                negative_count = len(recent_data[recent_data[sentiment_col] == 'negative'])
                
                positive_pct = (positive_count / total_tweets) * 100
                negative_pct = (negative_count / total_tweets) * 100
                
                # Afficher les alertes en temps réel
                col1, col2 = st.columns(2)
                
                with col1:
                    if negative_pct >= negative_threshold:
                        st.error(f"⚠️ ALERTE: {negative_pct:.1f}% des tweets récents sont négatifs!")
                    else:
                        st.info(f"✓ Niveau de tweets négatifs normal: {negative_pct:.1f}%")
                
                with col2:
                    if positive_pct >= positive_threshold:
                        st.success(f"📈 ALERTE: {positive_pct:.1f}% des tweets récents sont positifs!")
                    else:
                        st.info(f"✓ Niveau de tweets positifs normal: {positive_pct:.1f}%")
                
                # Afficher l'historique des alertes
                if not alerts_df.empty:
                    st.subheader("Historique des alertes")
                    
                    # Formater le dataframe des alertes pour l'affichage
                    alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
                    alerts_df = alerts_df.sort_values('timestamp', ascending=False)
                    
                    # Créer un dataframe pour l'affichage
                    display_alerts = pd.DataFrame()
                    display_alerts['Horodatage'] = alerts_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    display_alerts['Type'] = alerts_df.apply(lambda x: "Négatif" if x['negative_alert'] else "Positif", axis=1)
                    display_alerts['% Négatif'] = alerts_df['negative_pct'].round(1).astype(str) + '%'
                    display_alerts['% Positif'] = alerts_df['positive_pct'].round(1).astype(str) + '%'
                    display_alerts['Total tweets'] = alerts_df['total_count']
                    
                    # Fonction pour colorer les lignes selon le type d'alerte
                    def color_alert_type(val):
                        if val == 'Négatif':
                            return 'background-color: rgba(255, 0, 0, 0.2)'
                        else:
                            return 'background-color: rgba(0, 255, 0, 0.2)'
                    
                    st.dataframe(display_alerts.head(10).style.applymap(color_alert_type, subset=['Type']))
            else:
                st.info("Pas assez de données récentes pour l'analyse des alertes.")
        
        # Tableau des tweets récents
        st.subheader("Tweets récents")
        
        # Sélectionner les colonnes pertinentes
        recent_tweets = df[['timestamp', 'user', 'text', sentiment_col]].tail(10).reset_index(drop=True)
        recent_tweets.columns = ['Timestamp', 'Utilisateur', 'Tweet', 'Sentiment']
        
        # Formater le timestamp
        recent_tweets['Timestamp'] = recent_tweets['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Ajouter des couleurs pour les sentiments
        def color_sentiment(val):
            if val == 'positive':
                return 'background-color: rgba(0, 255, 0, 0.2)'
            elif val == 'negative':
                return 'background-color: rgba(255, 0, 0, 0.2)'
            else:
                return 'background-color: rgba(200, 200, 200, 0.2)'
        
        st.dataframe(recent_tweets.style.applymap(color_sentiment, subset=['Sentiment']))
        
        # Afficher l'heure de la dernière mise à jour
        st.text(f"Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Boucle de rafraîchissement
    placeholder = st.empty()
    
    with placeholder.container():
        update_dashboard()
    
    # Rafraîchissement automatique
    if st.button('Rafraîchir maintenant'):
        with placeholder.container():
            update_dashboard()
    
    st.text(f"Le tableau de bord se rafraîchit automatiquement toutes les {refresh_interval} secondes")
    
    # Boucle de rafraîchissement automatique
    while True:
        time.sleep(refresh_interval)
        with placeholder.container():
            update_dashboard() 