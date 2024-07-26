import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import anthropic
import json

# Configurazione di Anthropic
client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])

def generate_forecast_with_claude(historical_data, forecast_periods, assumptions, seasonality, kpi_prevision):
    data_str = json.dumps(historical_data)
    prompt = f"""
    Dato il seguente storico di dati finanziari: {data_str}

    Considerate le seguenti assumptions fornite dall'utente:

    - Previsioni di variazioni future: {kpi_percentages}
    - Eventuale stagionalità: {seasonality}
    - Eventuali informazioni aggiuntive: {assumptions}

    Genera una previsione per i prossimi {forecast_periods} periodi per ciascuna voce di bilancio.
    Considera tutte le informazioni fornite e le possibili relazioni tra le voci.

    Fornisci il risultato come una tabella in formato Markdown, includendo i dati storici e le previsioni.
    Usa il formato della data YYYY-MM-DD.

    Dopo la tabella, fornisci una breve spiegazione di come le ipotesi hanno influenzato le previsioni.
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

st.title('Advanced Financial Rolling Forecast Generator')

# Definizione delle voci di bilancio
balance_items = ['Valore della produzione',
    '+/- Variazione delle rimanenze',
    '- Costi esterni',
    'Valore aggiunto',
    '- Costi per il personale',
    'EBITDA',
    '- Costi non monetari',
    'EBIT',
    '+/- Proventi ed oneri finanziari',
    'Risultato ante imposte',
    '- Imposte',
    'Utile d\'esercizio']

kpi_percentages = [
    'Percentuale variazione ricavi (su base annua)',
    'Percentuale variazione costo del venduto (su base annua)',
    'Percentuale variazione costo del personale (su base annua)'
]

st.header("Inserimento dati ultimo bilancio annuale")

date = st.date_input("Data di bilancio")
data = {}

for item in balance_items:
    data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"new_{item}")

st.header("Inserisci le previsioni future")
kpi = {}
for item in kpi_percentages:
    kpi[item] = st.number_input(f"{item} (%)", value=0.0, step=1.0, key=f"new_{item}")

# Input per le assumptions
assumptions = st.text_area("Inserisci informazioni aggiuntive per la previsione:", 
                           "Es. Prevediamo investimenti per, o assunzioni di 2 collaboratori, ecc...")
seasonality = st.text_area("Descrivi eventuale stagionalità:", "Es. Prevediamo la maggior parte dei ricavi ad Agosto, o la maggior parte dei costi a settembre.")

# Input per il numero di mesi del forecast
forecast_months = st.number_input('Numero di mesi per il rolling forecast', min_value=1, max_value=24, value=6)


if st.button('Genera Forecast', key="new_forecast"):
    historical_data = [{"Data": date.strftime("%Y-%m-%d"), **data}]
    
    forecast_result = generate_forecast_with_claude(historical_data, forecast_months, assumptions, seasonality, kpi_percentages)
    
    st.subheader("Previsione e Spiegazione")
    st.markdown(forecast_result)

