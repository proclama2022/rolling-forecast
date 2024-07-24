import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import generate_forecast_with_claude
from io import StringIO

def generate_sales_forecast(extracted_data, forecast_period):
    st.subheader("Dati Storici Ricavi")
    historical_data = st.text_area("Inserisci i dati storici dei ricavi degli ultimi 12 mesi (formato CSV: Anno,Mese,Ricavi)")

    st.subheader("Assunzioni di Crescita Ricavi")
    revenue_growth = st.number_input("Crescita annuale dei ricavi (%)", min_value=-100.0, max_value=1000.0, step=0.1)

    if st.button("Genera Previsione Vendite"):
        growth_assumptions = f"Crescita ricavi: {revenue_growth}%"

        forecast_csv = generate_forecast_with_claude("ricavi", historical_data, "", growth_assumptions, forecast_period)

        try:
            df = pd.read_csv(StringIO(forecast_csv))

            # Rinomina la colonna se necessario
            if 'ricavi_Totali' in df.columns:
                df = df.rename(columns={'ricavi_Totali': 'Ricavi'})

        except (pd.errors.EmptyDataError, ValueError) as e:
            st.error(f"Errore durante la lettura del forecast: {e}")
            return None

        st.dataframe(df)

        # Grafico a barre per i ricavi
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Mese'] + ' ' + df['Anno'].astype(str), y=df['Ricavi'], name='Ricavi'))
        fig.update_layout(title='Previsione Ricavi', yaxis_title='Ricavi')
        st.plotly_chart(fig)

        st.download_button(label="Scarica previsione ricavi come CSV", data=forecast_csv, file_name="previsione_ricavi.csv", mime="text/csv")

        return df

    return None
