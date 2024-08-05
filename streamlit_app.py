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

def calculate_sum(data, items):
    return sum(data[item] for item in items)

st.title('Advanced Financial Rolling Forecast Generator')

# Struttura del bilancio con gruppi e voci
balance_structure = [
    ("Ricavi", [
        '+ Vendite di prodotti o servizi',
        '+ Altri ricavi'
    ]),
    ("Costi variabili", [
        '- Costi delle materie prime',
        '- Costi di produzione diretti',
        '- Costi di distribuzione e vendita variabili'
    ]),
    ("Margine lordo", []),  # Voce derivata
    ("Costi fissi", [
        '- Affitti',
        '- Utenze (elettricità, acqua, gas)',
        '- Manutenzione e riparazioni',
        '- Spese amministrative generali'
    ]),
    ("Costi del personale", [
        '- Salari e stipendi',
        '- Contributi previdenziali',
        '- Altri benefici del personale'
    ]),
    ("Spese operative", [
        '- Spese di marketing e pubblicità',
        '- Spese di viaggio e rappresentanza',
        '- Spese di ricerca e sviluppo',
        '- Spese legali e professionali'
    ]),
    ("EBITDA", []),  # Voce derivata
    ("Ammortamenti e svalutazioni", [
        '- Ammortamento di immobilizzazioni materiali e immateriali',
        '- Svalutazioni di asset'
    ]),
    ("EBIT", []),  # Voce derivata
    ("Interessi passivi e finanziari", [
        '- Interessi su prestiti e mutui',
        '- Altri costi finanziari'
    ]),
    ("Risultato operativo (EBT)", []),  # Voce derivata
    ("Tasse e imposte", [
        '- Imposte sul reddito',
        '- Altre imposte (IVA, imposte locali)'
    ]),
    ("Risultato netto", [])  # Voce derivata
]

st.header("Inserimento dati ultimo bilancio annuale")

date = st.date_input("Data di bilancio")
data = {}
derived_values = {}

# Funzione per calcolare e mostrare le voci derivate
def show_derived_value(label, value):
    st.markdown(f"**{label}: {value:.2f} €**")
    derived_values[label] = value

# Inserimento dati e calcolo voci derivate
ricavi = costi_variabili = costi_fissi = costi_personale = spese_operative = ammortamenti = interessi = imposte = 0

for group, items in balance_structure:
    st.subheader(group)
    if items:  # Se ci sono voci da inserire
        for item in items:
            data[item] = st.number_input(f"{item} (€)", value=0.0, step=1000.0, key=f"new_{item}")
        
        # Aggiorniamo le variabili per il calcolo delle voci derivate
        if group == "Ricavi":
            ricavi = calculate_sum(data, items)
        elif group == "Costi variabili":
            costi_variabili = calculate_sum(data, items)
        elif group == "Costi fissi":
            costi_fissi = calculate_sum(data, items)
        elif group == "Costi del personale":
            costi_personale = calculate_sum(data, items)
        elif group == "Spese operative":
            spese_operative = calculate_sum(data, items)
        elif group == "Ammortamenti e svalutazioni":
            ammortamenti = calculate_sum(data, items)
        elif group == "Interessi passivi e finanziari":
            interessi = calculate_sum(data, items)
        elif group == "Tasse e imposte":
            imposte = calculate_sum(data, items)
    else:  # Se è una voce derivata, la calcoliamo e mostriamo
        if group == "Margine lordo":
            margine_lordo = ricavi - costi_variabili
            show_derived_value(group, margine_lordo)
        elif group == "EBITDA":
            ebitda = margine_lordo - costi_fissi - costi_personale - spese_operative
            show_derived_value(group, ebitda)
        elif group == "EBIT":
            ebit = ebitda - ammortamenti
            show_derived_value(group, ebit)
        elif group == "Risultato operativo (EBT)":
            ebt = ebit - interessi
            show_derived_value(group, ebt)
        elif group == "Risultato netto":
            risultato_netto = ebt - imposte
            show_derived_value(group, risultato_netto)

# KPI e previsioni future
st.header("Inserisci le previsioni future")
kpi_percentages = [
    'Percentuale variazione ricavi (su base annua)',
    'Percentuale variazione costo del venduto (su base annua)',
    'Percentuale variazione costo del personale (su base annua)'
]

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
    historical_data = [{
        "Data": date.strftime("%Y-%m-%d"),
        **data,
        **derived_values
    }]
    
    forecast_result = generate_forecast_with_claude(historical_data, forecast_months, assumptions, seasonality, kpi_percentages)
    
    st.subheader("Previsione e Spiegazione")
    st.markdown(forecast_result)