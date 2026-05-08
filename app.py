import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والخلفية (إعادة الصورة)
st.set_page_config(page_title="Bébé Sympa", layout="wide")

# استبدل رابط الصورة برابط مباشر يعمل إذا أردت تغييرها
bg_img = "https://www.transparenttextures.com/patterns/dark-matter.png" 

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{bg_img}");
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }}
    /* تلوين الخانات داخل الجداول */
    [data-testid="stDataFrame"] {{
        background: rgba(30, 33, 36, 0.9);
        border: 2px solid #ffa500;
        border-radius: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية الأساسية
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except: return None

def load_data():
    s = get_sheet()
    if s:
        df = pd.DataFrame(s.get_all_records())
        if not df.empty:
            df.columns = df.columns.str.strip()
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def save_entry(row):
    s = get_sheet()
    if s:
        s.append_row(row)
        st.cache_resource.clear()

# 3. بناء الواجهة (الأقسام الخمسة)
try:
    df = load_data()
    st.title("🛡️ نظام الرقابة الشامل - Bébé Sympa")

    tabs = st.tabs(["📥 استلام من منزل", "📤 إرسال جديد", "🏢 المخزن", "💰 كشف حساب", "📜 السجل (History)"])

    # --- نافذة الاستلام ---
    with tabs[0]:
        st.subheader("🏠 استلام بضاعة جاهزة")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
            for h in homes:
                with st.expander(f"🏠 منزل: {h}"):
                    h_df = df[df['المنزل'] == h]
                    for prd in h_df['المنتج'].unique():
                        out_q = h_df[(h_df['المنتج'] == prd) & (h_df['الحالة'].isin(['ct', 'fn']))]['الكمية'].sum()
                        in_q = h_df[(h_df['المنتج'] == prd) & (h_df['الحالة'] == 'st')]['الكمية'].sum()
                        rem = out_q - in_q
                        if rem > 0:
                            st.write(f"**{prd}** (المتبقي بذمتهم: {int(rem)})")
                            q = st.number_input(f"استلام {prd}", min_value=0, key=f"in_{h}_{prd}")
                            if st.button("حفظ ✅", key=f"b_{h}_{prd}"):
                                save_entry([q, prd, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.rerun()

    # --- نافذة الإرسال ---
    with tabs[1]:
        st.subheader("📤 إرسال بضاعة للمنازل")
        with st.form("form_out"):
            f_h = st.text_input("اسم المنزل")
            f_p = st.text_input("اسم المنتج")
            f_q = st.number_input("الكمية", min_value=1)
            f_s = st.selectbox("الحالة", ["ct", "fn"])
            if st.form_submit_button("إرسال الآن 🚀"):
                save_entry([f_q, f_p, f_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_s])
                st.rerun()

    # --- نافذة المخزن (مع التلوين البصري) ---
    with tabs[2]:
        st.subheader("🏢 رصيد المخزن")
        if not df.
