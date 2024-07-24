import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import anthropic

# Configurazione di Anthropic (assicurati di avere una chiave API valida)
client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])

def generate_forecast_with_claude(historical_data, forecast_periods, assumptions):
    data_str = historical_data.to_json(orient='records')
    prompt = f"""
    Dato il seguente storico di dati finanziari: {data_str}

    E considerate le seguenti assumptions fornite dall'utente:
    {assumptions}

    Genera una previsione per i prossimi {forecast_periods} periodi per ciascuna voce di bilancio.
    Considera trend, stagionalità, possibili relazioni tra le voci e le assumptions fornite.
    Fornisci il risultato come una lista di dizionari, ciascuno contenente le previsioni per tutte le voci di bilancio.
    Includi anche una breve spiegazione di come le assumptions hanno influenzato le previsioni.

    Formato di risposta:
    {{
        "forecast": [
            {{"Ricavi": float, "Costi Materie Prime": float, "Costi del Personale": float, "Altri Costi Operativi": float}},
            ...
        ],
        "explanation": "string"
    }}
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        messages=[
        {"role": "user", "content": prompt}
    ],
        max_tokens=4096,
    )
    print(response)
    return eval(response.content)

st.title('Advanced Financial Rolling Forecast Generator')

# Definizione delle voci di bilancio
balance_items = ['Ricavi', 'Costi Materie Prime', 'Costi del Personale', 'Altri Costi Operativi']

# Input per le assumptions
assumptions = st.text_area("Inserisci le assumptions per la previsione (es. crescita del mercato, nuovi prodotti, cambiamenti nei costi):", 
                           "Prevediamo una crescita del mercato del 5% annuo. Lanceremo un nuovo prodotto nel secondo trimestre che dovrebbe aumentare i ricavi del 10%. I costi delle materie prime potrebbero aumentare del 3% a causa dell'inflazione.")

# Creazione delle tab
tab1, tab2 = st.tabs(["Nuovo Forecast", "Aggiorna Forecast Esistente"])

with tab1:
    st.header("Nuovo Forecast")
    
    date = st.date_input("Data di bilancio")
    data = {}
    for item in balance_items:
        data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"new_{item}")
    
    if st.button('Genera Forecast', key="new_forecast"):
        historical_data = pd.DataFrame([data], index=[date])
        
        forecast_periods = st.number_input('Numero di periodi da prevedere', min_value=1, max_value=12, value=3, key="new_periods")
        forecast_result = generate_forecast_with_claude(historical_data, forecast_periods, assumptions)
        
        forecast_dates = pd.date_range(start=date + timedelta(days=1), periods=forecast_periods, freq='M')
        forecast_data = pd.DataFrame(forecast_result['forecast'], index=forecast_dates)
        
        full_data = pd.concat([historical_data, forecast_data])
        
        st.subheader("Previsione")
        st.dataframe(full_data)
        
        st.subheader("Spiegazione della previsione")
        st.write(forecast_result['explanation'])
        
        # Visualizzazione
        fig = go.Figure()
        for item in balance_items:
            fig.add_trace(go.Scatter(x=full_data.index, y=full_data[item], name=item))
        fig.update_layout(title='Rolling Forecast', xaxis_title='Data', yaxis_title='Valore (€)')
        st.plotly_chart(fig)

with tab2:
    st.header("Aggiorna Forecast Esistente")
    
    uploaded_file = st.file_uploader("Carica il file CSV del forecast esistente", type="csv")
    
    if uploaded_file is not None:
        existing_forecast = pd.read_csv(uploaded_file, index_col=0, parse_dates=True)
        st.dataframe(existing_forecast)
        
        st.subheader("Inserisci i nuovi dati di bilancio")
        new_date = st.date_input("Data di aggiornamento", key="update_date")
        new_data = {}
        for item in balance_items:
            new_data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"update_{item}")
        
        if st.button('Aggiorna Forecast', key="update_forecast"):
            updated_historical = existing_forecast.copy()
            updated_historical.loc[new_date] = new_data
            updated_historical = updated_historical.sort_index()
            
            remaining_periods = len(existing_forecast) - len(updated_historical)
            if remaining_periods > 0:
                forecast_result = generate_forecast_with_claude(updated_historical, remaining_periods, assumptions)
                forecast_dates = pd.date_range(start=new_date + timedelta(days=1), periods=remaining_periods, freq='M')
                new_forecast_data = pd.DataFrame(forecast_result['forecast'], index=forecast_dates)
                
                updated_forecast = pd.concat([updated_historical, new_forecast_data])
            else:
                updated_forecast = updated_historical
            
            st.subheader("Forecast Aggiornato")
            st.dataframe(updated_forecast)
            
            if remaining_periods > 0:
                st.subheader("Spiegazione della previsione aggiornata")
                st.write(forecast_result['explanation'])
            
            # Visualizzazione
            fig = go.Figure()
            for item in balance_items:
                fig.add_trace(go.Scatter(x=updated_forecast.index, y=updated_forecast[item], name=item))
            fig.update_layout(title='Rolling Forecast Aggiornato', xaxis_title='Data', yaxis_title='Valore (€)')
            st.plotly_chart(fig)

st.markdown("""
Questa app genera o aggiorna un rolling forecast basato su dati di bilancio specifici e assumptions fornite dall'utente.
Utilizza Claude 3.5 Sonnet per produrre previsioni che tengono conto delle relazioni tra le diverse voci di bilancio e delle assumptions fornite.
""")