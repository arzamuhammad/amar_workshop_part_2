"""
Case 2 — Paid Rejection Dashboard (Streamlit in Snowflake)
Amar Bank Workshop Part 2

Dashboard demografi & funnel loan-origination di atas VW_PAID_REJECTION.
Dijalankan sebagai Streamlit in Snowflake (SiS). Data di-agregasi di SQL
(bukan tarik 100k baris ke client) agar cepat.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Paid Rejection Dashboard", layout="wide", page_icon="🏦")
session = get_active_session()

SRC = "AMAR_WORKSHOP_P2.REJECTION.VW_PAID_REJECTION"

# ---------- styling ----------
st.markdown("""
<style>
.main {background-color:#f5f7fa;}
h1,h2,h3 {color:#11567F;}
[data-testid="stMetric"]{background:linear-gradient(135deg,#11567F,#29B5E8);
  padding:16px;border-radius:12px;color:white;}
[data-testid="stMetricLabel"]{color:#e8f4fb;}
</style>
""", unsafe_allow_html=True)

st.title("🏦 Amar Bank — Paid Rejection Dashboard")
st.caption("Analisa funnel loan-origination, penolakan, dan demografi. Sumber: VW_PAID_REJECTION")


@st.cache_data(ttl=600)
def q(sql: str) -> pd.DataFrame:
    return session.sql(sql).to_pandas()

# ---------- filters ----------
with st.sidebar:
    st.header("Filter")
    cities = q(f"SELECT DISTINCT CITY FROM {SRC} ORDER BY 1")["CITY"].tolist()
    types = q(f"SELECT DISTINCT APP_TYPE FROM {SRC} ORDER BY 1")["APP_TYPE"].tolist()
    sel_city = st.multiselect("Kota", cities, default=cities)
    sel_type = st.multiselect("Tipe Aplikasi", types, default=types)

def where():
    c = "','".join(sel_city) if sel_city else ""
    t = "','".join(sel_type) if sel_type else ""
    return f"WHERE CITY IN ('{c}') AND APP_TYPE IN ('{t}')"

W = where()

# ---------- KPI ----------
kpi = q(f"""
SELECT COUNT(*) N, SUM(IS_PAIDOUT) PAID, SUM(IS_REJECTED) REJ,
       SUM(LOAN_AMOUNT) AMT, AVG(PROB_DEFAULT) PD
FROM {SRC} {W}
""").iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Aplikasi", f"{int(kpi.N):,}")
c2.metric("Approval Rate", f"{kpi.PAID/kpi.N*100:.1f}%")
c3.metric("Reject Rate", f"{kpi.REJ/kpi.N*100:.1f}%")
c4.metric("Total Diajukan", f"Rp {kpi.AMT/1e9:.1f} M")
c5.metric("Avg PD", f"{kpi.PD:.3f}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Funnel", "🚫 Reject Analysis", "👥 Demografi", "🗺️ Geo & Risk"])

with tab1:
    st.subheader("Funnel Konversi")
    f = q(f"""SELECT FUNNEL_STAGE, COUNT(*) N FROM {SRC} {W} GROUP BY 1""")
    order = ["Pending", "Dropoff", "Rejected", "Accepted", "Printed", "PaidOut"]
    f["ord"] = f.FUNNEL_STAGE.map({s: i for i, s in enumerate(order)})
    f = f.sort_values("ord")
    fig = go.Figure(go.Funnel(y=f.FUNNEL_STAGE, x=f.N, textinfo="value+percent initial",
                              marker={"color": "#29B5E8"}))
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tren Aplikasi per Bulan")
    tr = q(f"""SELECT CREATED_MONTH, COUNT(*) N, SUM(IS_PAIDOUT) PAID
               FROM {SRC} {W} GROUP BY 1 ORDER BY 1""")
    fig2 = px.area(tr, x="CREATED_MONTH", y=["N", "PAID"], labels={"value": "Jumlah"},
                   color_discrete_sequence=["#11567F", "#29B5E8"])
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Alasan Penolakan")
    r = q(f"""SELECT REJECT_REASON, COUNT(*) N FROM {SRC} {W}
              WHERE IS_REJECTED=1 AND REJECT_REASON IS NOT NULL GROUP BY 1 ORDER BY 2 DESC""")
    colA, colB = st.columns(2)
    colA.plotly_chart(px.bar(r, x="N", y="REJECT_REASON", orientation="h",
                             color="N", color_continuous_scale="Blues"), use_container_width=True)
    colB.plotly_chart(px.pie(r, names="REJECT_REASON", values="N", hole=0.5,
                             color_discrete_sequence=px.colors.sequential.Blues_r), use_container_width=True)
    st.subheader("Reject Rate per Kota")
    rr = q(f"""SELECT CITY, ROUND(SUM(IS_REJECTED)/COUNT(*)*100,1) REJECT_PCT FROM {SRC} {W} GROUP BY 1 ORDER BY 2 DESC""")
    st.plotly_chart(px.bar(rr, x="CITY", y="REJECT_PCT", color="REJECT_PCT",
                           color_continuous_scale="Reds"), use_container_width=True)

with tab3:
    st.subheader("Distribusi Demografi")
    c1, c2 = st.columns(2)
    age = q(f"SELECT AGE_BAND, COUNT(*) N FROM {SRC} {W} GROUP BY 1 ORDER BY 1")
    c1.plotly_chart(px.bar(age, x="AGE_BAND", y="N", title="Umur",
                           color_discrete_sequence=["#29B5E8"]), use_container_width=True)
    inc = q(f"SELECT INCOME_BAND, COUNT(*) N FROM {SRC} {W} GROUP BY 1")
    c2.plotly_chart(px.bar(inc, x="INCOME_BAND", y="N", title="Income Band",
                           color_discrete_sequence=["#11567F"]), use_container_width=True)
    c3, c4 = st.columns(2)
    edu = q(f"SELECT EDUCATION, COUNT(*) N FROM {SRC} {W} GROUP BY 1 ORDER BY 2 DESC")
    c3.plotly_chart(px.pie(edu, names="EDUCATION", values="N", title="Pendidikan", hole=0.4), use_container_width=True)
    occ = q(f"SELECT OCCUPATION, COUNT(*) N FROM {SRC} {W} GROUP BY 1 ORDER BY 2 DESC")
    c4.plotly_chart(px.bar(occ, x="N", y="OCCUPATION", orientation="h", title="Pekerjaan",
                           color_discrete_sequence=["#29B5E8"]), use_container_width=True)
    st.subheader("Approval Rate: Income Band × Umur (heatmap)")
    hm = q(f"""SELECT INCOME_BAND, AGE_BAND, ROUND(SUM(IS_PAIDOUT)/COUNT(*)*100,1) APPROVAL
               FROM {SRC} {W} GROUP BY 1,2""")
    piv = hm.pivot(index="INCOME_BAND", columns="AGE_BAND", values="APPROVAL")
    st.plotly_chart(px.imshow(piv, text_auto=True, color_continuous_scale="Blues",
                              aspect="auto"), use_container_width=True)

with tab4:
    st.subheader("Sebaran Aplikasi (peta)")
    geo = q(f"""SELECT CITY, AVG(LATITUDE) LAT, AVG(LONGITUDE) LON, COUNT(*) N,
                ROUND(SUM(IS_PAIDOUT)/COUNT(*)*100,1) APPROVAL
                FROM {SRC} {W} GROUP BY 1""")
    fig = px.scatter_mapbox(geo, lat="LAT", lon="LON", size="N", color="APPROVAL",
                            hover_name="CITY", color_continuous_scale="RdYlGn",
                            size_max=45, zoom=4, mapbox_style="carto-positron")
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Distribusi Probability of Default")
    pdd = q(f"SELECT PROB_DEFAULT FROM {SRC} {W} SAMPLE (20000 ROWS)")
    st.plotly_chart(px.histogram(pdd, x="PROB_DEFAULT", nbins=40,
                                 color_discrete_sequence=["#11567F"]), use_container_width=True)

st.caption("Amar Bank Workshop Part 2 · Streamlit in Snowflake · data sintetis")
