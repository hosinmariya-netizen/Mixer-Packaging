import streamlit as st
import pandas as pd
import requests
from io import StringIO
from urllib.parse import quote

st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", page_icon="🏗️", layout="centered")
st.markdown("<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)

sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"

sheets = [
    ("السلع", "📦"),
    ("الكراس", "📋"),
]

for name, icon in sheets:
    st.markdown(f"### {icon} {name}")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            df = pd.read_csv(StringIO(r.text))
            st.dataframe(df, use_container_width=True)
            st.info(f"عدد السجلات: {len(df)}")
        else:
            st.error(f"خطأ {r.status_code}")
    except Exception as e:
        st.error(f"خطأ: {e}")
    st.divider()
