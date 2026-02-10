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
                    continue
                
                # estrai solo i valori numerici disponibili
                df_close = df_raw[["Close"]].tail(historical_period)
                df_close = df_close[pd.to_numeric(df_close["Close"], errors="coerce").notna()]
                
                if len(df_close) == 0:
                    row["STATUS"] = "NO NUMERIC DATA"
                    rows.append(row)
                    continue


                # --------------------------
                # Pulizia serie
                # --------------------------
                df_close = df_raw[["Close"]].tail(historical_period)
                df_close["Close"] = pd.to_numeric(df_close["Close"], errors="coerce")
                df_close = df_close.dropna()

                if len(df_close) < 10:
                    row["ON MKT"] = float(df_close["Close"].iloc[-1].round(2)) if len(df_close) > 0 else np.nan
                    row["MIN"] = float(df_close["Close"].min().round(2)) if len(df_close) > 0 else np.nan
                    row["AVG"] = float(df_close["Close"].mean().round(2)) if len(df_close) > 0 else np.nan
                    row["MAX"] = float(df_close["Close"].max().round(2)) if len(df_close) > 0 else np.nan
                    row["FORECAST MIN"] = row["MIN"]
                    row["FORECAST VALUE"] = row["ON MKT"]
                    row["FORECAST MAX"] = row["MAX"]
                    row["Δ % FORECAST"] = 0
                    row["STATUS"] = "TOO SHORT FOR ARIMA"
                    rows.append(row)
                    continue

                row["ON MKT"] = float(df_close["Close"].iloc[-1].round(2))
                row["MIN"] = float(df_close["Close"].min().round(2))
                row["AVG"] = float(df_close["Close"].mean().round(2))
                row["MAX"] = float(df_close["Close"].max().round(2))

                # --------------------------
                # ARIMA + fallback
                # --------------------------
                try:
                    forecast, conf = run_arima(df_close["Close"], forecast_period)
                    row["FORECAST MIN"] = float(conf.iloc[-1, 0].round(2))
                    row["FORECAST VALUE"] = float(forecast.iloc[-1].round(2))
                    row["FORECAST MAX"] = float(conf.iloc[-1, 1].round(2))
                    row["Δ % FORECAST"] = float(
                        ((row["FORECAST VALUE"] - row["ON MKT"]) / row["ON MKT"] * 100).round(2)
                    )
                except Exception:
                    # fallback sicuro
                    row["FORECAST MIN"] = row["MIN"]
                    row["FORECAST VALUE"] = row["ON MKT"]
                    row["FORECAST MAX"] = row["MAX"]
                    row["Δ % FORECAST"] = 0
                    row["STATUS"] = "ARIMA FALLBACK"

            except Exception:
                row["STATUS"] = "ERROR"

            rows.append(row)

    df = pd.DataFrame(rows)

    # ================================
    # COLORAZIONE
    # ================================
    def color_rows(row):
        styles = []
        for col in row.index:
            if col == "FORECAST VALUE" and not pd.isna(row[col]):
                styles.append(
                    "color: blue; font-weight: bold" if row[col] > row["ON MKT"] else "color: red; font-weight: bold"
                )
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

    # ================================
    # ALTEZZA DINAMICA
    # ================================
    row_height = 35
    header_height = 40
    table_height = header_height + row_height * len(df)

    st.dataframe(
        df.style.apply(color_rows, axis=1),
        use_container_width=True,
        height=table_height
    )

else:
    st.info("👈 Imposta i parametri e premi **Applica**")
