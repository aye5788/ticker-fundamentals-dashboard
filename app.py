import streamlit as st
import pandas as pd
import requests
import altair as alt
import datetime

API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

@st.cache_data(ttl=3600)
def fetch_profile(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data(ttl=3600)
def fetch_ratios_ttm(ticker):
    url = f"{BASE_URL}/ratios-ttm/{ticker}?apikey={API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data(ttl=3600)
def fetch_key_metrics_ttm(ticker):
    url = f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}"
    return requests.get(url).json()[0]

@st.cache_data(ttl=3600)
def fetch_income_statement(ticker, period="annual"):
    url = f"{BASE_URL}/income-statement/{ticker}?period={'quarter' if period=='quarterly' else 'annual'}&limit=12&apikey={API_KEY}"
    df = pd.DataFrame(requests.get(url).json())
    if df.empty: return df
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")

@st.cache_data(ttl=86400)
def fetch_sector_pe_snapshot():
    for i in range(10):
        date = (datetime.datetime.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/sector-pe-snapshot?date={date}&apikey={API_KEY}"
        res = requests.get(url)
        if res.status_code == 200 and res.json():
            return res.json()
    return []

# --- UI ---
st.set_page_config(page_title="Fundamentals Dashboard", layout="wide")
st.title("📊 Fundamentals Dashboard")

ticker = st.text_input("Enter a ticker", "AAPL").strip().upper()

if ticker:
    with st.spinner("Loading..."):
        profile = fetch_profile(ticker)
        ratios = fetch_ratios_ttm(ticker)
        key_metrics = fetch_key_metrics_ttm(ticker)
        income_annual = fetch_income_statement(ticker, "annual")
        income_quarterly = fetch_income_statement(ticker, "quarterly")
        sector_pe_data = fetch_sector_pe_snapshot()

    st.subheader(f"{profile.get('companyName')} ({ticker})")
    c1, c2, c3 = st.columns(3)
    c1.metric("Sector", profile.get("sector", "–"))
    c2.metric("Industry", profile.get("industry", "–"))
    cap = profile.get("mktCap")
    c3.metric("Market Cap", f"${cap:,.0f}" if cap else "–")

    st.markdown("### 🔑 Key Ratios")
    basic = {
        "PE Ratio": ratios.get("priceEarningsRatioTTM"),
        "PEG Ratio": ratios.get("priceEarningsToGrowthRatioTTM"),
        "ROE": ratios.get("returnOnEquityTTM"),
        "Current Ratio": ratios.get("currentRatioTTM"),
        "Debt/Equity": ratios.get("debtEquityRatioTTM"),
    }
    st.table(pd.DataFrame.from_dict(basic, orient="index", columns=["Value"]).style.format("{:.2f}"))

    st.markdown("### 📈 Profitability & Valuation")
    prof_data = {
        "P/B Ratio": ratios.get("priceToBookRatioTTM"),
        "ROA": ratios.get("returnOnAssetsTTM"),
        "Gross Margin": ratios.get("grossProfitMarginTTM"),
        "Operating Margin": ratios.get("operatingProfitMarginTTM"),
        "Net Margin": ratios.get("netProfitMarginTTM"),
        "Interest Coverage": ratios.get("interestCoverageTTM"),
    }
    st.table(pd.DataFrame.from_dict(prof_data, orient="index", columns=["Value"]).style.format("{:.2f}"))

    st.markdown("### 📊 Revenue & Net Income")
    interval = st.radio("Interval", ["Annual", "Quarterly"], horizontal=True)
    df = income_annual if interval == "Annual" else income_quarterly
    if not df.empty:
        chart_df = df[["date", "revenue", "netIncome"]].melt(id_vars="date", var_name="Metric", value_name="Amount")
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("yearmonth(date):T", title="Date"),
            xOffset="Metric",
            y=alt.Y("Amount:Q", title="USD"),
            color="Metric:N",
            tooltip=["Metric", "date:T", alt.Tooltip("Amount:Q", format=",.0f")]
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No income data available.")

    st.markdown("### 🔁 YoY Growth (Revenue & Net Income)")
    if not income_annual.empty:
        y = income_annual.copy()
        y["Year"] = y["date"].dt.year
        y["Revenue YoY %"] = y["revenue"].pct_change() * 100
        y["Net Income YoY %"] = y["netIncome"].pct_change() * 100
        ydf = y[["Year", "Revenue YoY %", "Net Income YoY %"]].dropna().set_index("Year").T
        st.dataframe(ydf.style.format("{:.2f}%"), use_container_width=True)

    st.markdown("### 🧾 Earnings & Cash Flow")
    eps = key_metrics.get("epsTTM")
    fcf = key_metrics.get("freeCashFlowTTM")
    div = profile.get("lastDiv")
    price = profile.get("price")
    dy = (div / price * 100) if div and price else None
    clean = {
        "EPS (TTM)": f"{eps:.2f}" if eps else "N/A",
        "Free Cash Flow (TTM)": f"${fcf:,.0f}" if fcf else "N/A",
        "Dividend Yield": f"{dy:.2f}%" if dy else "N/A"
    }
    st.table(pd.DataFrame.from_dict(clean, orient="index", columns=["Value"]))

    st.markdown("### 🏷️ Sector P/E Comparison")
    sector = profile.get("sector")
    match = next((s for s in sector_pe_data if s.get("sector") == sector), None)
    if match:
        sector_pe = match.get("pe")
        company_pe = ratios.get("priceEarningsRatioTTM")
        st.table(pd.DataFrame({
            "Company P/E": [company_pe],
            f"{sector} Sector Avg P/E": [sector_pe]
        }).T.rename(columns={0: "Value"}).style.format("{:.2f}"))
    else:
        st.info(f"No sector P/E found for {sector}")

    st.caption("Data via Financial Modeling Prep — https://financialmodelingprep.com")

