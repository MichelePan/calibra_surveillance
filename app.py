import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="SURVEILLANCE Portfolio",
    layout="wide"
)

# ================================
# TICKERS
# ================================
TICKERS = {
    "ALPHABET INC": "GOOGL",
    "AMAZON": "AMZN",
    "AMERICA AIRLINES": "AAL",
    "ALIBABA GROUP HOLDING": "BABA",
    "BANK OF AMERICA CORP": "BAC",
    "NETFLIX": "NFLX",
    "NVIDIA": "NVDA",
    "TESLA": "TSLA"
}

# ================================
# FUNZIONE CLOSE
# ================================
def extract_close_column(df):
    if 'Close' in df.columns:
        return df[['Close']]
    raise ValueError("Close non trovata")

# ================================
# UI
# ================================
st.title("📈 SURVEILLANCE Portfolio – Stock Screener")

with st.sidebar:
    st.header("Parametri")

    historical_period = st.selectbox(
        "Numero valori storici",
        [120, 360, 720],
        index=0
    )

    forecast_period = st.selectbox(
        "Previsione futura (giorni)",
        [30, 60, 120],
        index=0
    )

    run = st.button("Applica")

# ================================
# LOGICA
# ================================
if run:

    results = []

    with st.spinner("Scarico dati e calcolo forecast..."):
        for ticker in TICKERS.values():
            try:
                df_raw = yf.download(
                    ticker,
                    period="5y",
                    interval="1d",
                    progress=False
                )

                on_mkt = float(df_raw['Close'].iloc[-1])

                df_close = extract_close_column(df_raw).dropna()
                df_close = df_close.tail(historical_period)

                model = ARIMA(df_close['Close'], order=(2, 0, 2)).fit()
                forecast = model.forecast(steps=forecast_period)
                conf = model.get_forecast(steps=forecast_period).conf_int()

                delta_pct = ((forecast.iloc[-1] - on_mkt) / on_mkt) * 100

                results.append({
                    "TICKER": ticker,
                    "ON MKT": on_mkt,
                    "MIN": df_close['Close'].min(),
                    "AVG": df_close['Close'].mean(),
                    "MAX": df_close['Close'].max(),
                    "FORECAST MIN": conf.iloc[-1, 0],
                    "FORECAST VALUE": forecast.iloc[-1],
                    "FORECAST MAX": conf.iloc[-1, 1],
                    "Δ % FORECAST": delta_pct
                })

            except Exception:
                pass

    df = pd.DataFrame(results)

    # ================================
    # STYLING
    # ================================
    # Rimuove righe con NaN (fondamentale)
    df = df.dropna().reset_index(drop=True)
    
    def highlight_forecast(row):
    styles = []
    for col in row.index:
        if col == "FORECAST VALUE":
            if row["FORECAST VALUE"] > row["ON MKT"]:
                styles.append("color: blue; font-weight: bold")
            else:
                styles.append("color: red; font-weight: bold")
        elif col == "Δ % FORECAST":
            if row["Δ % FORECAST"] > 20:
                styles.append("color: green; font-weight: bold")
            elif row["Δ % FORECAST"] < 0:
                styles.append("color: magenta; font-weight: bold")
            else:
                styles.append("")
        else:
            styles.append("")
    return styles
    
    styled = df.style.apply(highlight_forecast, axis=1)
    
    st.dataframe(styled, use_container_width=True)

else:
    st.info("👈 Imposta i parametri e premi **Applica**")
