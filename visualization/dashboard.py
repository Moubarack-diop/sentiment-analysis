#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import os
import numpy as np
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fonction pour charger le CSS personnalisé
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "style.css")
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
            "size": 100000,  # Limite à 1000 résultats
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger le CSS personnalisé
load_css()

# Titre de l'application avec style personnalisé
st.markdown('<h1 class="main-title">📊 Analyse de Sentiment en Temps Réel - Tweets sur les Tensions Commerciales</h1>', unsafe_allow_html=True)

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
        
        # Utiliser la colonne 'sentiment'
        sentiment_col = "sentiment"
        
        # Calculer les métriques
        total_tweets = len(df)
        positive_count = df[df[sentiment_col] == 'positive'].shape[0]
        negative_count = df[df[sentiment_col] == 'negative'].shape[0]
        neutral_count = df[df[sentiment_col] == 'neutral'].shape[0]
        
        positive_pct = round(100 * positive_count / total_tweets, 1) if total_tweets > 0 else 0
        negative_pct = round(100 * negative_count / total_tweets, 1) if total_tweets > 0 else 0
        neutral_pct = round(100 * neutral_count / total_tweets, 1) if total_tweets > 0 else 0
        
        # Affichage des métriques principales avec des cartes stylisées
        st.markdown("### Métriques clés")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total des tweets</h3>
                <p>{total_tweets}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card positive">
                <h3>Tweets positifs</h3>
                <p>{positive_pct}%</p>
                <small>{positive_count} tweets</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card negative">
                <h3>Tweets négatifs</h3>
                <p>{negative_pct}%</p>
                <small>{negative_count} tweets</small>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card neutral">
                <h3>Tweets neutres</h3>
                <p>{neutral_pct}%</p>
                <small>{neutral_count} tweets</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Section des graphiques avec style amélioré
        st.markdown('<div class="chart-section"><h2>Répartition des sentiments</h2>', unsafe_allow_html=True)
        
        # Graphique de répartition des sentiments (Donut chart)
        sentiment_counts = df[sentiment_col].value_counts().reset_index()
        sentiment_counts.columns = ['Sentiment', 'Count']
        
        # Traduction des sentiments pour l'affichage
        sentiment_mapping = {'positive': 'Positif', 'negative': 'Négatif', 'neutral': 'Neutre'}
        sentiment_counts['Sentiment'] = sentiment_counts['Sentiment'].map(sentiment_mapping)
        
        # Création du donut chart
        fig = px.pie(sentiment_counts, values='Count', names='Sentiment',
                    color='Sentiment',
                    color_discrete_map={'Positif':'#10B981', 'Neutre':'#6B7280', 'Négatif':'#EF4444'},
                    hole=0.6)
        
        # Personnalisation du graphique
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=0, b=0, l=0, r=0),
            height=400,
            annotations=[dict(text=f'{total_tweets}<br>Tweets', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        # Afficher le graphique avec une largeur personnalisée
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Évolution des sentiments au fil du temps avec style amélioré
        st.markdown('<div class="chart-section"><h2>Évolution des sentiments au fil du temps</h2>', unsafe_allow_html=True)
        
        # Regrouper par intervalle de temps (5 minutes)
        df['time_bucket'] = df['timestamp'].dt.floor('5min')
        
        sentiment_over_time = df.groupby(['time_bucket', sentiment_col]).size().unstack(fill_value=0)
        
        # Créer une figure avec des zones colorées sous les courbes
        fig = go.Figure()
        
        if 'positive' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(
                x=sentiment_over_time.index, 
                y=sentiment_over_time['positive'],
                mode='lines',
                name='Positif',
                line=dict(width=3, color='#10B981'),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.2)'
            ))
        
        if 'neutral' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(
                x=sentiment_over_time.index, 
                y=sentiment_over_time['neutral'],
                mode='lines',
                name='Neutre',
                line=dict(width=3, color='#6B7280'),
                fill='tozeroy',
                fillcolor='rgba(107, 114, 128, 0.2)'
            ))
        
        if 'negative' in sentiment_over_time.columns:
            fig.add_trace(go.Scatter(
                x=sentiment_over_time.index, 
                y=sentiment_over_time['negative'],
                mode='lines',
                name='Négatif',
                line=dict(width=3, color='#EF4444'),
                fill='tozeroy',
                fillcolor='rgba(239, 68, 68, 0.2)'
            ))
        
        # Personnalisation du graphique
        fig.update_layout(
            xaxis_title='Temps',
            yaxis_title='Nombre de tweets',
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=10, b=0, l=0, r=0),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(230, 230, 230, 0.5)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(230, 230, 230, 0.5)',
                rangemode='nonnegative'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Hashtags les plus fréquents avec style amélioré
        st.markdown('<div class="chart-section"><h2>Top 10 des hashtags</h2>', unsafe_allow_html=True)
        
        # Extraire tous les hashtags
        all_hashtags = []
        for hashtags in df['hashtags']:
            if hashtags:
                all_hashtags.extend(hashtags)
        
        if all_hashtags:
            hashtag_counts = pd.Series(all_hashtags).value_counts().reset_index()
            hashtag_counts.columns = ['Hashtag', 'Count']
            hashtag_counts = hashtag_counts.head(10)  # Top 10
            
            # Créer un graphique à barres horizontales avec des couleurs dégradées
            fig = px.bar(hashtag_counts, 
                         y='Hashtag', 
                         x='Count',
                         orientation='h',
                         color='Count',
                         color_continuous_scale=['#3B82F6', '#1E40AF'],
                         labels={'Count': 'Nombre d\'occurrences', 'Hashtag': ''})
            
            # Personnalisation du graphique
            fig.update_layout(
                margin=dict(t=10, b=0, l=0, r=10),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(230, 230, 230, 0.5)'
                ),
                yaxis=dict(
                    showgrid=False,
                    autorange="reversed"
                ),
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Aucun hashtag trouvé dans les données")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Section d'alertes de sentiment avec style amélioré
        if show_alerts:
            st.markdown('<div class="chart-section"><h2>Système d\'alertes de sentiment</h2>', unsafe_allow_html=True)
            
            # Vérification des seuils sur les données récentes
            recent_data = df[df['timestamp'] > (datetime.now() - timedelta(minutes=30))]
            
            if not recent_data.empty:
                # Calculer les pourcentages
                total_tweets = len(recent_data)
                positive_count = len(recent_data[recent_data[sentiment_col] == 'positive'])
                negative_count = len(recent_data[recent_data[sentiment_col] == 'negative'])
                
                positive_pct = (positive_count / total_tweets) * 100
                negative_pct = (negative_count / total_tweets) * 100
                
                # Afficher les alertes en temps réel avec un style amélioré
                col1, col2 = st.columns(2)
                
                with col1:
                    if negative_pct >= negative_threshold:
                        st.markdown(f'''
                        <div class="alert-box negative">
                            <div class="alert-icon">⚠️</div>
                            <div class="alert-content">
                                <p><strong>ALERTE:</strong> {negative_pct:.1f}% des tweets récents sont négatifs!</p>
                                <small>{negative_count} tweets négatifs sur {total_tweets} au total</small>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="alert-box info">
                            <div class="alert-icon">✓</div>
                            <div class="alert-content">
                                <p>Niveau de tweets négatifs normal: {negative_pct:.1f}%</p>
                                <small>{negative_count} tweets négatifs sur {total_tweets} au total</small>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                
                with col2:
                    if positive_pct >= positive_threshold:
                        st.markdown(f'''
                        <div class="alert-box positive">
                            <div class="alert-icon">📈</div>
                            <div class="alert-content">
                                <p><strong>ALERTE:</strong> {positive_pct:.1f}% des tweets récents sont positifs!</p>
                                <small>{positive_count} tweets positifs sur {total_tweets} au total</small>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="alert-box info">
                            <div class="alert-icon">✓</div>
                            <div class="alert-content">
                                <p>Niveau de tweets positifs normal: {positive_pct:.1f}%</p>
                                <small>{positive_count} tweets positifs sur {total_tweets} au total</small>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                
                # Afficher l'historique des alertes avec style amélioré
                if not alerts_df.empty:
                    st.markdown('<h3 style="margin-top: 20px;">Historique des alertes</h3>', unsafe_allow_html=True)
                    
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
                            return 'background-color: rgba(239, 68, 68, 0.2)'
                        else:
                            return 'background-color: rgba(16, 185, 129, 0.2)'
                    
                    st.dataframe(display_alerts.head(10).style.applymap(color_alert_type, subset=['Type']), use_container_width=True)
            else:
                st.info("Pas assez de données récentes pour l'analyse des alertes.")
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Tableau des tweets récents avec style amélioré
        st.markdown('<div class="chart-section"><h2>Tweets récents</h2>', unsafe_allow_html=True)
        
        # Sélectionner les colonnes pertinentes
        recent_tweets = df[['timestamp', 'user', 'text', sentiment_col]].tail(10).reset_index(drop=True)
        recent_tweets.columns = ['Timestamp', 'Utilisateur', 'Tweet', 'Sentiment']
        
        # Formater le timestamp
        recent_tweets['Timestamp'] = recent_tweets['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Traduire les sentiments pour l'affichage
        sentiment_mapping = {'positive': 'Positif', 'negative': 'Négatif', 'neutral': 'Neutre'}
        recent_tweets['Sentiment'] = recent_tweets['Sentiment'].map(sentiment_mapping)
        
        # Ajouter des couleurs pour les sentiments
        def color_sentiment(val):
            if val == 'Positif':
                return 'background-color: rgba(16, 185, 129, 0.2)'
            elif val == 'Négatif':
                return 'background-color: rgba(239, 68, 68, 0.2)'
            else:
                return 'background-color: rgba(107, 114, 128, 0.2)'
        
        st.dataframe(recent_tweets.style.applymap(color_sentiment, subset=['Sentiment']), use_container_width=True)
        
        # Afficher l'heure de la dernière mise à jour
        st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 0.8rem;'>Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Barre de progression pour le rafraîchissement
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown(f"<h3>Rafraîchissement automatique</h3>", unsafe_allow_html=True)
    
    # Bouton de rafraîchissement avec style amélioré
    if st.button('Rafraîchir maintenant', key='refresh_button'):
        with st.spinner('Rafraîchissement des données...'):
            placeholder = st.empty()
            with placeholder.container():
                update_dashboard()
    
    # Barre de progression pour le rafraîchissement automatique
    st.markdown(f"<p style='margin-bottom: 5px;'>Le tableau de bord se rafraîchit automatiquement toutes les {refresh_interval} secondes</p>", unsafe_allow_html=True)
    progress_bar = st.markdown("""
    <div class="refresh-progress-bar">
        <div class="refresh-progress" id="progress"></div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const progressBar = document.querySelector('#progress');
            const totalTime = {refresh_interval};
            let timeLeft = totalTime;
            
            function updateProgress() {
                const percentage = (timeLeft / totalTime) * 100;
                progressBar.style.width = percentage + '%';
                timeLeft -= 1;
                
                if (timeLeft < 0) {
                    timeLeft = totalTime;
                }
            }
            
            setInterval(updateProgress, 1000);
            updateProgress();
        });
    </script>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Pied de page
    st.markdown('<div class="footer">Projet d\'analyse de sentiment en temps réel - © 2025</div>', unsafe_allow_html=True)
    
    # Boucle de rafraîchissement
    placeholder = st.empty()
    
    with placeholder.container():
        update_dashboard()
    
    # Boucle de rafraîchissement automatique
    while True:
        time.sleep(refresh_interval)
        with placeholder.container():
            update_dashboard() 