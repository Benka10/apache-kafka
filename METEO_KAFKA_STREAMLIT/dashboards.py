import streamlit as st
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Streamlit app
def dashboard(dashboard_type: str):
    # Default settings
    st.set_page_config(
        page_title="Real-time Weather Data App",
        page_icon="⛅",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Run the Streamlit app
    st.title(str.upper(dashboard_type) + " : Weather Data")

    # Add Logo
    st.sidebar.image("images/logo.png", width=250)

    # Sidebar with user instructions
    st.sidebar.markdown(
        """
        This app fetches real-time weather data from Accuweather APIs.
        This produce messages to the Kafka topic and consume messages from the Kafka topic, 
        then displays real-time weather data from Kafka messages.
        """
    )

    # Display weather data in the main section
    st.header("Real-Time Weather Data with Kafka + Streamlit")

def create_dashboard(data):
    fig = make_subplots(rows=2, cols=1)

    fig.add_trace(go.Scatter(x=data['time'], y=data['temperature'], mode='lines', name='Temperature'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data['time'], y=data['humidity'], mode='lines', name='Humidity'), row=2, col=1)

    fig.update_layout(title='Weather Data Dashboard')
    return fig