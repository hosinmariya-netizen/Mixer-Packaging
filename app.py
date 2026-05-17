import streamlit as st
import pandas as pd
from urllib.parse import quote

st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", page_icon="🏗️", layout="centered")

st.markdown("<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)
st.write("مرحباً بك! يتم الآن جلب بيانات الورشة الحالية:")

st.markdown("### 📦 جدول السلع والمخزون الحالي")

sheet_id = "1B6f0_W0Z7yUwa-N0mKkVA_mKkvWp1_7k-xkvaawpw9M"
sheet_name = quote("السلع")  # ← هذا يحل مشكلة الأحرف العربية
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

try:
    df = pd.read_csv(url)
    st.dataframe(df, use_container_width=True)
    st.info(f"إجمالي عدد الأصناف: {len(df)} صنف.")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
