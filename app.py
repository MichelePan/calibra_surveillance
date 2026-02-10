import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

# ================================
# CONFIG STREAMLIT
# ================================
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
    "TESLA": "TSLA",
}

# ================================
# CACHE DOWNLOAD
# ================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker):
    return yf.download(
        ticker,
        period="5y",
        interval="1d",
        progress=False
    )

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
                df_raw = load_data(ticker)

                if df_raw.empty or "Close" not in df_raw.columns:
                    continue

                on_mkt = float(df_raw["Close"].iloc[-1])

                df_close = df_raw[["Close"]].dropna().tail(historical_period)

                if len(df_close) < 20:
                    continue

                model = ARIMA(df_close["Close"], order=(2, 0, 2)).fit()
                forecast = model.forecast(steps=forecast_period)
                conf = model.get_forecast(steps=forecast_period).conf_int()

                delta_pct = ((forecast.iloc[-1] - on_mkt) / on_mkt) * 100

                results.append({
                    "TICKER": ticker,
                    "ON MKT": on_mkt,
                    "MIN": df_close["Close"].min(),
                    "AVG": df_close["Close"].mean(),
                    "MAX": df_close["Close"].max(),
                    "FORECAST MIN": conf.iloc[-1, 0],
                    "FORECAST VALUE": forecast.iloc[-1],
                    "FORECAST MAX": conf.iloc[-1, 1],
                    "Δ % FORECAST": delta_pct
                })

            except Exception:
                continue

    if len(results) == 0:
        st.warning("Nessun ticker valido elaborato.")
        st.stop()

    df = pd.DataFrame(results).round(2)

    # ================================
    # COLORAZIONE (STREAMLIT SAFE)
    # ================================
    def color_rows(row):
        colors = []
        for col in row.index:
            if col == "FORECAST VALUE":
                if row["FORECAST VALUE"] > row["ON MKT"]:
                    colors.append("color: blue; font-weight: bold")
                else:
                    colors.append("color: red; font-weight: bold")
            elif col == "Δ % FORECAST":
                if row["Δ % FORECAST"] > 20:
                    colors.append("color: green; font-weight: bold")
                elif row["Δ % FORECAST"] < 0:
                    colors.append("color: magenta; font-weight: bold")
                else:
                    colors.append("")
            else:
                colors.append("")
        return colors

    styled_df = df.style.apply(color_rows, axis=1)

    st.dataframe(styled_df, use_container_width=True)

else:
    st.info("👈 Imposta i parametri e premi **Applica**")
