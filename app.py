import streamlit as st
import pandas as pd

st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", page_icon="🏗️", layout="centered")

st.markdown("<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)
st.write("مرحباً بك! يتم الآن جلب بيانات الورشة الحالية:")

sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"

# ── الورقة الأولى (السلع / المراجع)
st.markdown("### 📦 جدول السلع والمخزون الحالي")
url1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
try:
    df1 = pd.read_csv(url1)
    st.dataframe(df1, use_container_width=True)
    st.info(f"إجمالي عدد الأصناف: {len(df1)} صنف.")
except Exception as e:
    st.error(f"خطأ: {e}")

st.divider()

# ── الورقة الثانية (History / التاريخ)
st.markdown("### 📋 سجل الإدخال والإخراج")
url2 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1"
try:
    df2 = pd.read_csv(url2)
    st.dataframe(df2, use_container_width=True)
except Exception as e:
    st.error(f"خطأ: {e}")
