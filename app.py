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
# TICKERS COMPLETI
# ================================
TICKERS = {
    "ALPHABET INC": "GOOGL",
    "AMAZON": "AMZN",
    "AMERICA AIRLINES": "AAL",
    "AMERICAN BATTERY TECHNOLOGY COMPANY": "ABAT",
    "ATOSSA THERAPEUTICS INC": "ATOS",
    "ALIBABA GROUP HOLDING": "BABA",
    "BANK OF AMERICA CORP": "BAC",
    "BEYOND MEAT": "BYND",
    "CENOVUS ENERGY INC": "CVE",
    "CERENCE": "CRNC",
    "CLEAN ENERGY FUELS CORP": "CLNE",
    "COMCAST CORPORATION": "CMCSA",
    "COTERRA ENERGY INC": "CTRA",
    "CRONOS GROUP INC": "CRON",
    "DELTA AIRLINES": "DAL",
    "DEVON ENERGY CORPORATION": "DVN",
    "EBAY INC": "EBAY",
    "FISERV": "FISV",
    "FORD MOTOR CO": "F",
    "HASBRO": "HAS",
    "HP INC": "HPQ",
    "HUNTINGTON BANCSHARES INC": "HBAN",
    "ICAHN ENTERPRISES LP": "IEP",
    "INCANNEX HEALTHCARE INC": "IXHL",
    "INTEL": "INTC",
    "IONIS PHARMACEUTICALS": "IONS",
    "KOSMOS ENERGY LTD": "KOS",
    "LYFT INC": "LYFT",
    "NETFLIX": "NFLX",
    "NEW FORTRESS ENERGY INC": "NFE",
    "NVIDIA": "NVDA",
    "PAYPAL HOLDINGS INC": "PYPL",
    "PELOTON INTERACTIVE": "PTON",
    "PINTEREST INC": "PINS",
    "REVIVA PHARMACEUTICALS HOLDING INC": "RVPH",
    "RIVIAN AUTOMOTIVE INC": "RIVN",
    "SNAP INC": "SNAP",
    "TARGET HOSPITAL CORP": "TH",
    "THE COCA-COLA COMPANY": "KO",
    "THE WALT DISNEY COMPANY": "DIS",
    "TESLA": "TSLA",
    "TILRAY BRANDS INC": "TLRY",
    "TRANSOCEAN LTD": "RIG",
    "TRAWS PHARMA INC": "TRAW",
    "UNIQURE NV": "QURE",
    "VITAL ENERGY INC": "VTLE"
}

# ================================
# CACHE DOWNLOAD YFINANCE
# ================================
@st.cache_data(ttl=3600)
def load_data(ticker):
    return yf.download(
        ticker,
        period="5y",
        interval="1d",
        progress=False
    )

# ================================
# CACHE ARIMA
# ================================
@st.cache_data(ttl=3600)
def run_arima(series, steps):
    model = ARIMA(series, order=(2, 0, 2)).fit()
    forecast = model.forecast(steps=steps)
    conf = model.get_forecast(steps=steps).conf_int()
    return forecast, conf

# ================================
# UI
# ================================
st.title("📈 SURVEILLANCE Portfolio – Stock Screener")

with st.sidebar:
    st.header("Parametri")
    historical_period = st.selectbox("Numero valori storici", [120, 360, 720])
    forecast_period = st.selectbox("Previsione futura (giorni)", [30, 60, 120])
    run = st.button("Applica")

# ================================
# LOGICA PRINCIPALE
# ================================
if run:
    rows = []

    with st.spinner("Calcolo in corso..."):
        for name, ticker in TICKERS.items():

            row = {
                "NAME": name,
                "TICKER": ticker,
                "ON MKT": np.nan,
                "MIN": np.nan,
                "AVG": np.nan,
                "MAX": np.nan,
                "FORECAST MIN": np.nan,
                "FORECAST VALUE": np.nan,
                "FORECAST MAX": np.nan,
                "Δ % FORECAST": np.nan,
                "STATUS": "OK"
            }

            try:
                df_raw = load_data(ticker)

                if df_raw.empty or "Close" not in df_raw.columns:
                    row["STATUS"] = "NO DATA"
                    rows.append(row)
                    con
