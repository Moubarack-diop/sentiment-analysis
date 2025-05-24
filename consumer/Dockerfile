FROM bitnami/spark:latest

USER root

ENV USER=root

# Installation des dépendances Python
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install kafka-python pyspark textblob nltk elasticsearch \
    && python3 -m nltk.downloader vader_lexicon \
    && python3 -m textblob.download_corpora

# Copie des fichiers de l'application
COPY . /opt/bitnami/spark/consumer/

WORKDIR /opt/bitnami/spark/consumer/

CMD ["python3", "sentiment_analyzer.py"] 