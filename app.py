import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

# ================================
# CONFIG
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
# CACHE
# ================================
@st.cache_data(ttl=3600)
def load_data(ticker):
    return yf.download(
        ticker,
        period="5y",
        interval="1d",
        progress=False
    )

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
# LOGICA
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
                    continue

                row["ON MKT"] = float(df_raw["Close"].iloc[-1])

                df_close = df_raw[["Close"]].dropna().tail(historical_period)

                if len(df_close) < 20:
                    row["STATUS"] = "INSUFFICIENT DATA"
                    rows.append(row)
                    continue

                forecast, conf = run_arima(df_close["Close"], forecast_period)

                row["MIN"] = float(df_close["Close"].min().round(2))
                row["AVG"] = float(df_close["Close"].mean().round(2))
                row["MAX"] = float(df_close["Close"].max().round(2))
                row["FORECAST MIN"] = conf.iloc[-1, 0]
                row["FORECAST VALUE"] = forecast.iloc[-1]
                row["FORECAST MAX"] = conf.iloc[-1, 1]
                row["Δ % FORECAST"] = (
                    (row["FORECAST VALUE"] - row["ON MKT"]) / row["ON MKT"] * 100
                )

            except Exception:
                row["STATUS"] = "ARIMA ERROR"

            rows.append(row)

    df = pd.DataFrame(rows).round(2)

    # ================================
    # COLORAZIONE
    # ================================
    def color_rows(row):
        styles = []
        for col in row.index:
            if col == "FORECAST VALUE" and not pd.isna(row[col]):
                if row[col] > row["ON MKT"]:
                    styles.append("color: blue; font-weight: bold")
                else:
                    styles.append("color: red; font-weight: bold")
            elif col == "Δ % FORECAST" and not pd.isna(row[col]):
                if row[col] > 20:
                    styles.append("color: green; font-weight: bold")
                elif row[col] < 0:
                    styles.append("color: magenta; font-weight: bold")
                else:
                    styles.append("")
            elif col == "STATUS" and row[col] != "OK":
                styles.append("color: orange; font-weight: bold")
            else:
                styles.append("")
        return styles

    row_height = 35          # px per riga (ottimale)
    header_height = 40       # header
    table_height = header_height + row_height * len(df)
    
    st.dataframe(
        df.style.apply(color_rows, axis=1),
        use_container_width=True,
        height=table_height
    )
    
else:
    st.info("👈 Imposta i parametri e premi **Applica**")
