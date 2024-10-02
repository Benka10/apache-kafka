import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
import streamlit as st
from dotenv import load_dotenv # type: ignore
import os
from environment import KAFKA_BROKER, KAFKA_TOPIC
from weather import fetch_weather_data
from dashboards import dashboard

# Charger les variables d'environnement
load_dotenv()

# Kafka DLQ Topic
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'weather_dlq')

# Fonction de callback en cas de succès d'envoi
def on_success(metadata):
    st.success(f"Message envoyé avec succès au topic {metadata.topic} sur la partition {metadata.partition}")

# Fonction de callback en cas d'échec d'envoi
def on_error(excp, producer, message):
    st.error(f"Erreur lors de l'envoi du message: {excp}")
    # Envoyer à la Dead Letter Queue
    try:
        producer.send(DLQ_TOPIC, message).add_callback(on_success).add_errback(lambda e: st.error(f"Erreur d'envoi à la DLQ: {e}"))
    except KafkaError as e:
        st.error(f"Erreur critique lors de l'envoi à la DLQ: {e}")

# Kafka producer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    retries=5,  # Add retries to handle failure
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def produce_kafka_messages(loc):
    # Créer un producteur Kafka
    producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER], retries=5)
    weather_data = fetch_weather_data(loc)

    if weather_data:
        res = json.dumps(weather_data).encode("utf-8")

        # Envoyer les données météo au topic Kafka
        producer.send(KAFKA_TOPIC, res).add_callback(on_success).add_errback(lambda excp: on_error(excp, producer, res))
        return res

    return False

if __name__ == '__main__':
    dashboard("producer")

    # Champ de saisie pour la localisation
    location = st.text_input('Location')

    # Bouton d'action
    action = st.button('Produce weather data to Kafka')

    if action:
        message = produce_kafka_messages(location)
        if message:
            st.success("Données météo produites à Kafka.")
        else:
            st.error("Erreur lors de la production des données.")
