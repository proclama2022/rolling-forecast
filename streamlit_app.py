import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import anthropic
import json

# Configurazione di Anthropic
client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])

def generate_forecast_with_claude(historical_data, forecast_periods, assumptions):
    data_str = json.dumps(historical_data)
    prompt = f"""
    Dato il seguente storico di dati finanziari: {data_str}

    E considerate le seguenti assumptions fornite dall'utente:
    {assumptions}

    Genera una previsione per i prossimi {forecast_periods} periodi per ciascuna voce di bilancio.
    Considera trend, stagionalità, possibili relazioni tra le voci e le assumptions fornite.

    Fornisci il risultato come una tabella in formato Markdown, includendo i dati storici e le previsioni.
    Usa il formato della data YYYY-MM-DD.

    Dopo la tabella, fornisci una breve spiegazione di come le assumptions hanno influenzato le previsioni.
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content

st.title('Advanced Financial Rolling Forecast Generator')

# Definizione delle voci di bilancio
balance_items = ['Ricavi', 'Costi Materie Prime', 'Costi del Personale', 'Altri Costi Operativi']

# Input per le assumptions
assumptions = st.text_area("Inserisci le assumptions per la previsione:", 
                           "Prevediamo una crescita del mercato del 5% annuo. Lanceremo un nuovo prodotto nel secondo trimestre che dovrebbe aumentare i ricavi del 10%. I costi delle materie prime potrebbero aumentare del 3% a causa dell'inflazione.")

# Input per il numero di mesi del forecast
forecast_months = st.number_input('Numero di mesi per il rolling forecast', min_value=1, max_value=24, value=6)

# Creazione delle tab
tab1, tab2 = st.tabs(["Nuovo Forecast", "Aggiorna Forecast Esistente"])

with tab1:
    st.header("Nuovo Forecast")
    
    date = st.date_input("Data di bilancio")
    data = {}
    for item in balance_items:
        data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"new_{item}")
    
    if st.button('Genera Forecast', key="new_forecast"):
        historical_data = [{"Data": date.strftime("%Y-%m-%d"), **data}]
        
        forecast_result = generate_forecast_with_claude(historical_data, forecast_months, assumptions)
        
        st.subheader("Previsione e Spiegazione")
        st.markdown(forecast_result)

with tab2:
    st.header("Aggiorna Forecast Esistente")
    
    st.subheader("Inserisci i nuovi dati di bilancio")
    new_date = st.date_input("Data di aggiornamento", key="update_date")
    new_data = {}
    for item in balance_items:
        new_data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"update_{item}")
    
    previous_forecast = st.text_area("Incolla il forecast precedente (in formato Markdown):", 
                                     "| Data | Ricavi | Costi Materie Prime | Costi del Personale | Altri Costi Operativi |\n|------|--------|---------------------|---------------------|------------------------|\n| 2024-01-01 | 100000 | 50000 | 30000 | 10000 |\n...")
    
    if st.button('Aggiorna Forecast', key="update_forecast"):
        # Convertiamo il forecast precedente in una lista di dizionari
        lines = previous_forecast.split('\n')[2:]  # Ignoriamo l'intestazione
        historical_data = []
        for line in lines:
            if line.strip():
                parts = line.split('|')
                if len(parts) == 6:  # Ci aspettiamo 6 parti: vuoto, data, e 4 valori
                    historical_data.append({
                        "Data": parts[1].strip(),
                        "Ricavi": float(parts[2].strip()),
                        "Costi Materie Prime": float(parts[3].strip()),
                        "Costi del Personale": float(parts[4].strip()),
                        "Altri Costi Operativi": float(parts[5].strip())
                    })
        
        # Aggiungiamo i nuovi dati
        historical_data.append({
            "Data": new_date.strftime("%Y-%m-%d"),
            **new_data
        })
        
        # Ordiniamo i dati per data
        historical_data.sort(key=lambda x: x["Data"])
        
        forecast_result = generate_forecast_with_claude(historical_data, forecast_months, assumptions)
        
        st.subheader("Forecast Aggiornato e Spiegazione")
        st.markdown(forecast_result)

st.markdown("""
Questa app genera o aggiorna un rolling forecast basato su dati di bilancio specifici e assumptions fornite dall'utente.
Utilizza Claude 3.5 Sonnet per produrre previsioni che tengono conto delle relazioni tra le diverse voci di bilancio e delle assumptions fornite.
Il risultato è presentato come una tabella Markdown seguita da una spiegazione testuale.
""")