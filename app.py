import streamlit as st
import pandas as pd

st.markdown("### 📦 جدول السلع والمخزون الحالي")

# استبدل /edit بـ /export
sheet_id = "1B6f0_W0Z7yUwa-N0mKkVA_mKkvWp1_7k-xkvaawpw9M"
sheet_name = "السلع"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

try:
    df = pd.read_csv(url)
    st.dataframe(df, use_container_width=True)
    st.info(f"إجمالي عدد الأصناف: {len(df)} صنف.")
except Exception as e:
    st.error(f"خطأ: {e}")
