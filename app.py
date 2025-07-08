import streamlit as st
import pandas as pd
import requests

# --- Config ---
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- Helper Functions ---

@st.cache_data(ttl=3600)
def fetch_fundamentals(ticker: str) -> pd.DataFrame:
    url = f"{BASE_URL}/ratios-ttm/{ticker.upper()}?apikey={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    latest = data[0]
    metrics = {
        "PE Ratio (TTM)": latest.get("priceEarningsRatioTTM"),
        "PEG Ratio": latest.get("priceEarningsToGrowthRatioTTM"),
        "ROE": latest.get("returnOnEquityTTM"),
        "Current Ratio": latest.get("currentRatioTTM"),
        "Debt/Equity": latest.get("debtEquityRatioTTM"),
    }
    return pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"])

@st.cache_data(ttl=3600)
def fetch_profile(ticker: str) -> dict:
    url = f"{BASE_URL}/profile/{ticker.upper()}?apikey={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data[0] if data else {}

@st.cache_data(ttl=3600)
def fetch_income_statement(ticker: str, period: str = "annual") -> pd.DataFrame:
    url = f"{BASE_URL}/income-statement/{ticker}?period={'quarter' if period=='quarterly' else 'annual'}&limit=12&apikey={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

# --- Streamlit UI ---
st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

ticker = st.text_input("Enter a ticker symbol", value="AAPL").strip().upper()

if ticker:
    with st.spinner(f"Loading data for {ticker}…"):
        profile = fetch_profile(ticker)
        metrics = fetch_fundamentals(ticker)

    if not profile:
        st.error(f"No data found for ticker `{ticker}`.")
        st.stop()

    # Display profile info
    st.subheader(f"{profile.get('companyName')} ({ticker})")
    cols = st.columns(3)
    cols[0].metric("Sector", profile.get("sector", "–"))
    cols[1].metric("Industry", profile.get("industry", "–"))
    mktcap = profile.get("mktCap")
    formatted_cap = f"${mktcap:,}" if mktcap else "–"
    cols[2].metric("Market Cap", formatted_cap)

    # Display ratios
    st.markdown("### Key Ratios (TTM)")
    st.table(metrics.style.format("{:.2f}"))

    # Revenue & Net Income Chart
    st.markdown("### Revenue & Net Income")
    interval = st.radio("Select time interval", ["Annual", "Quarterly"], horizontal=True)

    income_df = fetch_income_statement(ticker, period=interval.lower())
    if not income_df.empty:
        chart_data = income_df[["date", "revenue", "netIncome"]].set_index("date")
        st.line_chart(chart_data.rename(columns={
            "revenue": "Revenue",
            "netIncome": "Net Income"
        }))
    else:
        st.warning("No income statement data available.")

    st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")

