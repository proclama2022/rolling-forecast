import streamlit as st
from sales_forecast import generate_sales_forecast
from cost_forecast import generate_cost_forecast
from utils import analyze_forecast_with_ai, extract_data_from_balance, parse_extracted_data
import pandas as pd
import plotly.graph_objects as go

st.title("Generatore di Forecast Finanziario")

# Caricamento del bilancio
uploaded_balance = st.file_uploader("Carica il tuo bilancio di verifica o bilancio CEE", type=['pdf', 'docx', 'xlsx', 'xls', 'txt'])
extracted_text = ""
if uploaded_balance:
    extracted_text = extract_data_from_balance(uploaded_balance)
    st.success("Bilancio caricato e testo estratto con successo!")  # Messaggio di conferma

# Criteri di estrazione
extraction_criteria = st.text_input("Inserisci i criteri di estrazione (es. 'Ricavi, Costi, Utile Netto')", "Ricavi, Costi, Utile Netto")

# Periodo di forecast
forecast_period = st.number_input("Numero di mesi da prevedere", min_value=1, max_value=36, value=36, step=1)

tab1, tab2, tab3, tab4 = st.tabs(["Previsione Vendite", "Previsione Costi", "Riepilogo", "Analisi AI"])

with tab1:
    st.header("Previsione Vendite")
    sales_forecast = generate_sales_forecast(extracted_text, forecast_period)

with tab2:
    st.header("Previsione Costi")
    cost_forecast = generate_cost_forecast(extracted_text, forecast_period)

with tab3:
    st.header("Riepilogo Finanziario")
    if sales_forecast is not None and cost_forecast is not None:
        combined_forecast = pd.merge(sales_forecast, cost_forecast, on=['Anno', 'Mese'])
        combined_forecast['Profitto'] = combined_forecast['Vendite_Totali'] - combined_forecast['Costi_Totali']

        st.dataframe(combined_forecast)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=combined_forecast['Mese'] + ' ' + combined_forecast['Anno'].astype(str),
                             y=combined_forecast['Vendite_Totali'], name='Vendite'))
        fig.add_trace(go.Bar(x=combined_forecast['Mese'] + ' ' + combined_forecast['Anno'].astype(str),
                             y=combined_forecast['Costi_Totali'], name='Costi'))
        fig.add_trace(go.Scatter(x=combined_forecast['Mese'] + ' ' + combined_forecast['Anno'].astype(str),
                                 y=combined_forecast['Profitto'], name='Profitto', yaxis='y2'))

        fig.update_layout(title='Riepilogo Finanziario',
                          yaxis_title='Euro',
                          yaxis2=dict(title='Profitto', overlaying='y', side='right'),
                          barmode='group')

        st.plotly_chart(fig)

        csv = combined_forecast.to_csv(index=False)
        st.download_button(label="Scarica riepilogo come CSV",
                           data=csv,
                           file_name="riepilogo_finanziario.csv",
                           mime="text/csv")
    else:
        st.write("Genera prima le previsioni di vendite e costi.")

with tab4:
    st.header("Analisi AI del Forecast")
    if sales_forecast is not None and cost_forecast is not None:
        if st.button("Genera Analisi AI"):
            extracted_data = parse_extracted_data(extracted_text, extraction_criteria)
            ai_analysis = analyze_forecast_with_ai(sales_forecast, cost_forecast, forecast_period)
            st.markdown(ai_analysis)

            st.download_button(label="Scarica Analisi AI come TXT",
                               data=ai_analysis,
                               file_name="analisi_ai_forecast.txt",
                               mime="text/plain")
    else:
        st.write("Genera prima le previsioni di vendite e costi per ottenere un'analisi AI.")
