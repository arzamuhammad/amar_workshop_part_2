"""
Case 3 — Loan Repayment / Payback Curve Dashboard (Streamlit in Snowflake)
Amar Bank Workshop Part 2 — pengganti "Look" Looker.

Membaca VW_PAYBACK_CURVE & VW_REPAYMENT_LONG. Menampilkan:
  - payback curve (kurva pelunasan kumulatif per bulan-ke-N)
  - perbandingan sumber CRM vs Bank
  - cohort heatmap (vintage analysis)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Payback Curve", layout="wide", page_icon="📈")
session = get_active_session()
SCH = "AMAR_WORKSHOP_P2.REPAYMENT"

st.markdown("""<style>
h1,h2,h3{color:#11567F;}
[data-testid="stMetric"]{background:linear-gradient(135deg,#11567F,#29B5E8);padding:14px;border-radius:12px;color:#fff;}
</style>""", unsafe_allow_html=True)

st.title("📈 Amar Bank — Loan Repayment / Payback Curve")
st.caption("Vintage analysis pelunasan pinjaman. Pengganti Looker Look — data live dari Snowflake.")


@st.cache_data(ttl=600)
def q(sql):
    return session.sql(sql).to_pandas()

with st.sidebar:
    st.header("Filter")
    types = q(f"SELECT DISTINCT APP_TYPE FROM {SCH}.VW_PAYBACK_CURVE ORDER BY 1")["APP_TYPE"].tolist()
    sel = st.multiselect("Tipe Aplikasi", types, default=types)
self = "','".join(sel)

kpi = q(f"""
SELECT COUNT(DISTINCT REF_NUM) N, SUM(LOAN_AMOUNT) PRINC
FROM {SCH}.LOAN_REPAYMENT_VINTAGE WHERE APP_TYPE IN ('{self}')""").iloc[0]
final = q(f"""SELECT ROUND(AVG(PAYBACK_RATE),3) R FROM {SCH}.VW_PAYBACK_CURVE
              WHERE MONTH_INDEX=24 AND APP_TYPE IN ('{self}')""").iloc[0].R
c1, c2, c3 = st.columns(3)
c1.metric("Total Loan", f"{int(kpi.N):,}")
c2.metric("Total Principal", f"Rp {kpi.PRINC/1e9:.1f} M")
c3.metric("Payback @ M24", f"{final*100:.1f}%")

tab1, tab2, tab3 = st.tabs(["Payback Curve", "CRM vs Bank", "Cohort Heatmap"])

with tab1:
    st.subheader("Kurva Pelunasan Kumulatif (per Tipe)")
    d = q(f"""SELECT MONTH_INDEX, APP_TYPE, ROUND(AVG(PAYBACK_RATE)*100,2) PAYBACK_PCT
              FROM {SCH}.VW_PAYBACK_CURVE WHERE APP_TYPE IN ('{self}')
              GROUP BY 1,2 ORDER BY 1""")
    st.plotly_chart(px.line(d, x="MONTH_INDEX", y="PAYBACK_PCT", color="APP_TYPE", markers=True,
                            labels={"MONTH_INDEX": "Bulan ke-", "PAYBACK_PCT": "Payback %"},
                            color_discrete_sequence=["#11567F", "#29B5E8", "#71D3DC"]),
                    use_container_width=True)

with tab2:
    st.subheader("Collection: CRM vs Bank (kumulatif per bulan)")
    d = q(f"""SELECT MONTH_INDEX, SUM(CUMULATIVE_CRM) CRM, SUM(CUMULATIVE_BANK) BANK
              FROM {SCH}.VW_REPAYMENT_LONG WHERE APP_TYPE IN ('{self}')
              GROUP BY 1 ORDER BY 1""")
    dm = d.melt("MONTH_INDEX", var_name="Sumber", value_name="Kumulatif")
    st.plotly_chart(px.line(dm, x="MONTH_INDEX", y="Kumulatif", color="Sumber", markers=True,
                            color_discrete_sequence=["#11567F", "#F7931E"]), use_container_width=True)
    st.info("Gap CRM vs Bank menandakan selisih pencatatan/timing — bahan rekonsiliasi tim collection.")

with tab3:
    st.subheader("Cohort Heatmap — Payback % per Cohort × Bulan")
    d = q(f"""SELECT TO_VARCHAR(COHORT_MONTH,'YYYY-MM') COHORT, MONTH_INDEX,
                 ROUND(AVG(PAYBACK_RATE)*100,1) PAYBACK
              FROM {SCH}.VW_PAYBACK_CURVE WHERE APP_TYPE IN ('{self}')
              GROUP BY 1,2""")
    piv = d.pivot(index="COHORT", columns="MONTH_INDEX", values="PAYBACK").sort_index()
    st.plotly_chart(px.imshow(piv, color_continuous_scale="Blues", aspect="auto",
                              labels={"x": "Bulan ke-", "y": "Cohort (bln disburse)", "color": "Payback %"}),
                    use_container_width=True)

st.caption("Amar Bank Workshop Part 2 · Streamlit in Snowflake · data sintetis")
