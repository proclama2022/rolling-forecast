import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import generate_forecast_with_claude
from io import StringIO  # Importazione esplicita di StringIO

def generate_cost_forecast(extracted_data, forecast_period):
    st.subheader("Dati Storici Costi")
    historical_data = st.text_area("Inserisci i dati storici dei costi degli ultimi 12 mesi (formato CSV: Anno,Mese,Costi_Totali)")

    st.subheader("Categorie di Costo")
    cost_categories = st.text_area("Inserisci le principali categorie di costo (una per riga)")

    st.subheader("Assunzioni di Crescita Costi")
    cost_growth = st.number_input("Crescita annuale dei costi (%)", min_value=-100.0, max_value=1000.0, step=0.1)

    if st.button("Genera Previsione Costi"):
        cost_info = f"Categorie di costo: {cost_categories}"
        growth_assumptions = f"Crescita costi: {cost_growth}%"

        forecast_csv = generate_forecast_with_claude("costi", historical_data, cost_info, growth_assumptions, forecast_period)

        try:
            df = pd.read_csv(StringIO(forecast_csv))  # Uso diretto di StringIO
        except pd.errors.EmptyDataError:
            st.error("La previsione generata è vuota. Controlla i dati in input.")
            return None

        st.dataframe(df)

        fig = go.Figure()
        for category in df.columns[3:]:  # Assumiamo che le prime 3 colonne siano Anno, Mese, Costi_Totali
            fig.add_trace(go.Bar(x=df['Mese'] + ' ' + df['Anno'].astype(str), y=df[category], name=category))
        fig.add_trace(go.Scatter(x=df['Mese'] + ' ' + df['Anno'].astype(str), y=df['Costi_Totali'], name='Costi Totali', yaxis='y2'))
        fig.update_layout(title='Previsione Costi', yaxis_title='Euro', yaxis2=dict(title='Costi Totali', overlaying='y', side='right'))
        st.plotly_chart(fig)

        st.download_button(label="Scarica previsione costi come CSV", data=forecast_csv, file_name="previsione_costi.csv", mime="text/csv")

        return df

    return None
