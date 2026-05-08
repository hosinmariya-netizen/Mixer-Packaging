import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        direction: rtl;
        background-image: url("https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(14, 17, 23, 0.92);
        z-index: 0;
    }
    .stApp > div {
        position: relative;
        z-index: 1;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1

def get_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    for col in ["الكمية","المنتج","العميل","منزل_الخياطة","منزل_التغليف","التاريخ","المرحلة"]:
        if col not in df.columns:
            df[col] = ""
    df["الكمية"] = pd.to_numeric(df["الكمية"], errors="coerce").fillna(0)
    return df

def add_row(row):
    get_sheet().append_row(row)

st.title("نظام إدارة الورشة - Bébé Sympa")
if st.button("تحديث"):
    st.cache_resource.clear()
    st.rerun()

df = get_data()
tab1, tab2, tab3, tab4 = st.tabs(["🧵 خياطة", "📦 تغليف", "📊 تقرير", "📜 سجل"])

with tab1:
    with st.form("sew"):
        c1,c2 = st.columns(2)
        name = c1.text_input("اسم العميل")
        prod = c2.text_input("المنتج")
        qt = st.number_input("الكمية",1)
        home = st.text_input("منزل الخياطة")
        if st.form_submit_button("تسجيل خياطة"):
            add_row([qt, prod, name, home, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "خياطة"])
            st.success("تم")

with tab2:
    with st.form("pac"):
        c1,c2 = st.columns(2)
        name = c1.text_input("اسم العميل")
        prod = c2.text_input("المنتج")
        qt = st.number_input("الكمية",1)
        home = st.text_input("منزل التغليف")
        if st.form_submit_button("تسجيل تغليف"):
            add_row([qt, prod, name, "", home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "تغليف"])
            st.success("تم")

with tab3:
    if not df.empty:
        sew = df[df["المرحلة"]=="خياطة"].groupby(["المنتج","منزل_الخياطة"])["الكمية"].sum()
        pac = df[df["المرحلة"]=="تغليف"].groupby(["المنتج","منزل_التغليف"])["الكمية"].sum()
        st.dataframe(sew)
        st.dataframe(pac)

with tab4:
    st.dataframe(df)
