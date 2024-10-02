import json
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import streamlit as st
from environment import KAFKA_BROKER, KAFKA_TOPIC
from dashboards import dashboard
from datetime import datetime, timedelta
from collections import deque

# Dead Letter Queue topic
DLQ_TOPIC = "dead_letter_queue"

# Example of sliding window logic
window_size = timedelta(minutes=5)
window_start = datetime.now()

def process_window(records):
    # Aggregate data and detect anomalies
    pass

consumer = KafkaConsumer('weather_data', bootstrap_servers='localhost:9092', api_version=(2, 5, 0))

window_data = []
for message in consumer:
    record = json.loads(message.value)
    window_data.append(record)

    if datetime.now() - window_start >= window_size:
        process_window(window_data)
        window_data.clear()
        window_start = datetime.now()


# Fenêtre temporelle pour l'agrégation (ex. 5 minutes)
time_window = timedelta(minutes=5)
data_window = deque()  # Utilisation d'une deque pour stocker les messages dans une fenêtre temporelle

# Fonction de gestion des erreurs avec envoi vers la Dead Letter Queue (DLQ)
def handle_error(message, error):
    st.error(f"Erreur lors du traitement du message : {error}")
    # Envoi à la Dead Letter Queue
    producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER])
    producer.send(DLQ_TOPIC, json.dumps({'error': str(error), 'message': message.value}).encode('utf-8'))
    producer.close()

# Processus des données météo en tenant compte de la fenêtre temporelle
def process_weather_data(message):
    try:
        data = message.value
        current_time = datetime.strptime(data['datetime'], "%Y-%m-%d %H:%M:%S")
        
        # Ajout du message dans la fenêtre temporelle
        data_window.append((current_time, data))

        # Suppression des messages hors fenêtre
        while data_window and (current_time - data_window[0][0]) > time_window:
            data_window.popleft()

        # Agrégation des données dans la fenêtre temporelle (exemple d'agrégation : moyenne de la température)
        temp_sum = sum([item[1]['temperature'] for item in data_window])
        temp_avg = temp_sum / len(data_window)

        # Mise à jour de l'interface Streamlit
        col1, col2, col3 = st.columns(3)
        col1.metric("Location", data['location'], data['country'])
        col2.metric("Weather", data['weather'])
        col3.metric("UVIndex", data['uvindex'])

        col1.metric(label="Température Moyenne (5 min)", value=f"{temp_avg:.2f} °{data['temperature_unit']}")
        col2.metric(label="RealFeel", value=f"{data['realfeel']} °{data['realfeel_unit']}", delta=data['realfeel_status'])
        col3.metric("Vent", f"{data['wind']} {data['wind_unit']}", f"{data['wind_dir']} direction")

        col1.metric("Précipitation", f"{data['precipitation']}%")
        col2.metric("Humidité", f"{data['humidity']}%")
        col3.metric("Humidité Intérieure", f"{data['indoor']}%")

        col1.metric("Pluie", f"{data['rain']}%")
        col2.metric("Tonnerre", f"{data['thunder']}%")
        col3.metric("Neige", f"{data['snow']}%")

        st.success(f"Dernière mise à jour : {data['datetime']}")
        
    except Exception as e:
        handle_error(message, e)

# Fonction de consommation des messages Kafka avec tolérance aux pannes
def consume_kafka_messages():
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            enable_auto_commit=True,  # Relecture automatique après crash
            auto_offset_reset='earliest',  # Relecture des anciens messages après redémarrage
            consumer_timeout_ms=1000  # Timeout pour ne pas bloquer
        )

        for message in consumer:
            process_weather_data(message)

    except KafkaError as e:
        st.error(f"Erreur Kafka : {e}")
        # En cas d'incident Kafka, on relance la consommation des messages
        consume_kafka_messages()

# Mise à jour du dashboard Streamlit
if __name__ == '__main__':
    dashboard("consumer")
    consume_kafka_messages()
