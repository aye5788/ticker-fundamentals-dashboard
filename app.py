import streamlit as st
import pandas as pd
import requests
import altair as alt

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
    base_metrics = {
        "PE Ratio (TTM)": latest.get("priceEarningsRatioTTM"),
        "PEG Ratio": latest.get("priceEarningsToGrowthRatioTTM"),
        "ROE": latest.get("returnOnEquityTTM"),
        "Current Ratio": latest.get("currentRatioTTM"),
        "Debt/Equity": latest.get("debtEquityRatioTTM"),
    }
    extra_metrics = {
        "P/B Ratio": latest.get("priceToBookRatioTTM"),
        "ROA": latest.get("returnOnAssetsTTM"),
        "Gross Margin": latest.get("grossProfitMarginTTM"),
        "Operating Margin": latest.get("operatingProfitMarginTTM"),
        "Net Margin": latest.get("netProfitMarginTTM"),
        "Interest Coverage": latest.get("interestCoverageTTM")
    }
    return pd.DataFrame.from_dict(base_metrics, orient="index", columns=["Value"]), pd.DataFrame.from_dict(extra_metrics, orient="index", columns=["Value"])

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
        base_ratios, extra_ratios = fetch_fundamentals(ticker)

    if not profile:
        st.error(f"No data found for ticker `{ticker}`.")
        st.stop()

    # --- Company Profile ---
    st.subheader(f"{profile.get('companyName')} ({ticker})")
    cols = st.columns(3)
    cols[0].metric("Sector", profile.get("sector", "–"))
    cols[1].metric("Industry", profile.get("industry", "–"))
    mktcap = profile.get("mktCap")
    formatted_cap = f"${mktcap:,}" if mktcap else "–"
    cols[2].metric("Market Cap", formatted_cap)

    # --- Key Ratios ---
    st.markdown("### Key Ratios (TTM)")
    st.table(base_ratios.style.format("{:.2f}"))

    # --- Expanded Metrics ---
    st.markdown("### Profitability & Valuation Metrics")
    st.table(extra_ratios.style.format("{:.2f}"))

    # --- Income Statement Chart ---
    st.markdown("### Revenue & Net Income")
    interval = st.radio("Select time interval", ["Annual", "Quarterly"], horizontal=True)

    income_df = fetch_income_statement(ticker, period=interval.lower())
    if not income_df.empty:
        chart_df = income_df[["date", "revenue", "netIncome"]].melt(
            id_vars="date",
            var_name="Metric",
            value_name="Amount"
        )

        base = alt.Chart(chart_df).encode(
            x=alt.X('yearmonth(date):T', title='Date'),
            y=alt.Y('Amount:Q', title='USD'),
            color=alt.Color('Metric:N', scale=alt.Scale(scheme='tableau10')),
            tooltip=["date:T", "Metric:N", "Amount:Q"]
        )

        bar = base.mark_bar()
        line = base.mark_line(point=True)

        st.altair_chart((bar + line).properties(width='container', height=400).configure_axisX(labelAngle=-45), use_container_width=True)

        # --- YoY Growth Table (Annual only, transposed) ---
        if interval == "Annual":
            yoy_df = income_df[["date", "revenue", "netIncome"]].copy()
            yoy_df["Revenue YoY %"] = yoy_df["revenue"].pct_change() * 100
            yoy_df["Net Income YoY %"] = yoy_df["netIncome"].pct_change() * 100
            yoy_df["Year"] = yoy_df["date"].dt.year
            display_df = yoy_df[["Year", "Revenue YoY %", "Net Income YoY %"]].dropna()

            # Transpose
            table = display_df.set_index("Year").T
            st.markdown("### YoY Growth (Revenue & Net Income)")
            st.dataframe(table.style.format("{:.2f}%"), use_container_width=True)
    else:
        st.warning("No income statement data available.")

    st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")

