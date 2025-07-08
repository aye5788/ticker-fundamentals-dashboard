import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime

# --- Config ---
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# --- Helper Functions ---
@st.cache_data(ttl=3600)
def fetch_profile(ticker: str):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}

@st.cache_data(ttl=3600)
def fetch_ratios_ttm(ticker: str):
    url = f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}

@st.cache_data(ttl=3600)
def fetch_key_metrics(ticker: str):
    url = f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else {}

@st.cache_data(ttl=3600)
def fetch_income_statement(ticker: str, period: str = "annual"):
    url = f"{BASE_URL}/income-statement/{ticker}?period={'quarter' if period=='quarterly' else 'annual'}&limit=12&apikey={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

@st.cache_data(ttl=3600)
def fetch_sector_pe_snapshot(date_str: str = None):
    if not date_str:
        date_str = datetime.datetime.today().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/sector-pe-snapshot?date={date_str}&apikey={API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# --- Streamlit UI ---
st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

ticker = st.text_input("Enter a ticker symbol", value="AAPL").strip().upper()

if ticker:
    with st.spinner(f"Loading data for {ticker}..."):
        profile = fetch_profile(ticker)
        ratios = fetch_ratios_ttm(ticker)
        key_metrics = fetch_key_metrics(ticker)
        income_annual = fetch_income_statement(ticker, "annual")
        income_quarterly = fetch_income_statement(ticker, "quarterly")
        sector_pe_list = fetch_sector_pe_snapshot()

    if not profile:
        st.error(f"No data found for ticker `{ticker}`.")
        st.stop()

    # --- Company Header ---
    st.subheader(f"{profile.get('companyName')} ({ticker})")
    cols = st.columns(3)
    cols[0].metric("Sector", profile.get("sector", "–"))
    cols[1].metric("Industry", profile.get("industry", "–"))
    mktcap = profile.get("mktCap")
    formatted_cap = f"${mktcap:,}" if mktcap else "–"
    cols[2].metric("Market Cap", formatted_cap)

    # --- Key Ratios ---
    st.markdown("### Key Ratios (TTM)")
    key_data = {
        "PE Ratio": ratios.get("priceEarningsRatioTTM"),
        "PEG Ratio": ratios.get("priceEarningsToGrowthRatioTTM"),
        "ROE": ratios.get("returnOnEquityTTM"),
        "Current Ratio": ratios.get("currentRatioTTM"),
        "Debt/Equity": ratios.get("debtEquityRatioTTM")
    }
    st.table(pd.DataFrame.from_dict(key_data, orient="index", columns=["Value"]).style.format("{:.2f}"))

    # --- Profitability & Valuation ---
    st.markdown("### Profitability & Valuation Metrics")
    extra_data = {
        "P/B Ratio": ratios.get("priceToBookRatioTTM"),
        "ROA": ratios.get("returnOnAssetsTTM"),
        "Gross Margin": ratios.get("grossProfitMarginTTM"),
        "Operating Margin": ratios.get("operatingProfitMarginTTM"),
        "Net Margin": ratios.get("netProfitMarginTTM"),
        "Interest Coverage": ratios.get("interestCoverageTTM")
    }
    st.table(pd.DataFrame.from_dict(extra_data, orient="index", columns=["Value"]).style.format("{:.2f}"))

    # --- Revenue & Net Income Chart ---
    st.markdown("### Revenue & Net Income")
    interval = st.radio("Select time interval", ["Annual", "Quarterly"], horizontal=True)
    selected_df = income_annual if interval == "Annual" else income_quarterly

    if not selected_df.empty:
        chart_df = selected_df[["date", "revenue", "netIncome"]].copy()
        chart_df = chart_df.melt(id_vars="date", var_name="Metric", value_name="Amount")

        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('yearmonth(date):T', title='Date'),
            xOffset='Metric',
            y=alt.Y('Amount:Q', title='USD'),
            color=alt.Color('Metric:N', scale=alt.Scale(scheme='tableau10')),
            tooltip=[
                alt.Tooltip("Metric:N"),
                alt.Tooltip("date:T"),
                alt.Tooltip("Amount:Q", format=",.0f")
            ]
        ).properties(width='container', height=400)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No income statement data available.")

    # --- YoY Growth Table (Annual only)
    if not income_annual.empty:
        yoy_df = income_annual[["date", "revenue", "netIncome"]].copy()
        yoy_df["Revenue YoY %"] = yoy_df["revenue"].pct_change() * 100
        yoy_df["Net Income YoY %"] = yoy_df["netIncome"].pct_change() * 100
        yoy_df["Year"] = yoy_df["date"].dt.year
        display_df = yoy_df[["Year", "Revenue YoY %", "Net Income YoY %"]].dropna()
        table = display_df.set_index("Year").T
        st.markdown("### YoY Growth (Revenue & Net Income)")
        st.dataframe(table.style.format("{:.2f}%"), use_container_width=True)

    # --- EPS, FCF, Dividend Yield
    st.markdown("### Earnings & Cash Flow Metrics")
    fcf = key_metrics.get("freeCashFlowTTM")
    eps = key_metrics.get("epsTTM")
    dividend_yield = profile.get("lastDiv") / profile.get("price") * 100 if profile.get("price") else None

    earnings_data = {
        "EPS (TTM)": eps,
        "Free Cash Flow (TTM)": fcf,
        "Dividend Yield": dividend_yield
    }
    st.table(pd.DataFrame.from_dict(earnings_data, orient="index", columns=["Value"]).style.format("{:.2f}"))

    # --- Sector PE Comparison
    st.markdown("### Sector P/E Comparison")
    sector_name = profile.get("sector")
    matched_sector = next((s for s in sector_pe_list if s.get("sector") == sector_name), None)
    if matched_sector:
        sector_pe = matched_sector.get("pe")
        company_pe = ratios.get("priceEarningsRatioTTM")
        pe_data = {
            "Company P/E": company_pe,
            f"{sector_name} Sector Avg P/E": sector_pe
        }
        st.table(pd.DataFrame.from_dict(pe_data, orient="index", columns=["Value"]).style.format("{:.2f}"))
    else:
        st.info(f"No sector P/E data found for sector '{sector_name}'.")

    st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")

