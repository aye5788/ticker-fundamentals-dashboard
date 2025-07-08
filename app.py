import streamlit as st
import pandas as pd
import requests

# --- Config ---
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- Helper functions ---
@st.cache_data(ttl=3600)
def fetch_fundamentals(ticker: str) -> pd.DataFrame:
    """Fetch key fundamental ratios from FMP and return a DataFrame."""
    url = f"{BASE_URL}/ratios-ttm/{ticker.upper()}?apikey={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    # Pick latest row
    latest = data[0]
    # Select a subset of ratios you care about:
    metrics = {
        "PE Ratio (TTM)": latest.get("priceEarningsRatioTTM"),
        "PEG Ratio":      latest.get("priceEarningsToGrowthRatioTTM"),
        "ROE":            latest.get("returnOnEquityTTM"),
        "Current Ratio":  latest.get("currentRatioTTM"),
        "Debt/Equity":    latest.get("debtEquityRatioTTM"),
    }
    df = pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"])
    return df

@st.cache_data(ttl=3600)
def fetch_profile(ticker: str) -> dict:
    """Fetch company profile (name, sector, market cap, etc.)"""
    url = f"{BASE_URL}/profile/{ticker.upper()}?apikey={API_KEY}"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data[0] if data else {}

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

    # Display header info
    st.subheader(f"{profile.get('companyName')} ({ticker})")
    cols = st.columns(3)
    cols[0].metric("Sector", profile.get("sector", "–"))
    cols[1].metric("Industry", profile.get("industry", "–"))
    cols[2].metric("Market Cap", f"${profile.get('mktCap'):,}" if profile.get("mktCap") else "–")

    # Show fundamentals table
    st.markdown("### Key Ratios (TTM)")
    st.table(metrics.style.format("{:.2f}"))

    # (Optional) Show more sections, e.g. historical income statement, balance sheet…

    # Footer / source
    st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")
