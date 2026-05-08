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
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
        return None

def get_data():
    sheet = get_sheet()
    if sheet is None:
        return pd.DataFrame()
    
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # تحقق من الأعمدة المطلوبة
        required_cols = ["الكمية", "المنتج", "العميل", "منزل_الخياطة", "منزل_التغليف", "التاريخ", "المرحلة"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        
        df["الكمية"] = pd.to_numeric(df["الكمية"], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        return pd.DataFrame()

def add_row(row):
    try:
        sheet = get_sheet()
        if sheet is not None:
            sheet.append_row(row)
    except Exception as e:
        st.error(f"خطأ في إضافة البيانات: {e}")

st.title("نظام إدارة الورشة - Bébé Sympa")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.rerun()

df = get_data()
tab1, tab2, tab3, tab4 = st.tabs(["🧵 خياطة", "📦 تغليف", "📊 تقرير", "📜 سجل"])

with tab1:
    st.subheader("تسجيل الخياطة")
    with st.form("sew"):
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم العميل")
        prod = c2.text_input("المنتج")
        qt = st.number_input("الكمية", 1, step=1)
        home = st.text_input("منزل الخياطة")
        
        if st.form_submit_button("✅ تسجيل خياطة"):
            if name and prod and home:
                add_row([qt, prod, name, home, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "خياطة"])
                st.success("✓ تم التسجيل بنجاح")
            else:
                st.warning("⚠️ يرجى ملء جميع الحقول")

with tab2:
    st.subheader("تسجيل التغليف")
    with st.form("pac"):
        c1, c2 = st.columns(2)
        name = c1.text_input("اسم العميل")
        prod = c2.text_input("المنتج")
        qt = st.number_input("الكمية", 1, step=1)
        home = st.text_input("منزل التغليف")
        
        if st.form_submit_button("✅ تسجيل تغليف"):
            if name and prod and home:
                add_row([qt, prod, name, "", home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "تغليف"])
                st.success("✓ تم التسجيل بنجاح")
            else:
                st.warning("⚠️ يرجى ملء جميع الحقول")

with tab3:
    st.subheader("📊 التقارير")
    if not df.empty:
        try:
            sew = df[df["المرحلة"] == "خياطة"].groupby(["المنتج", "منزل_الخياطة"])["الكمية"].sum()
            pac = df[df["المرحلة"] == "تغليف"].groupby(["المنتج", "منزل_التغليف"])["الكمية"].sum()
            
            st.write("**📍 إحصائيات الخياطة:**")
            st.dataframe(sew, use_container_width=True)
            
            st.write("**📍 إحصائيات التغليف:**")
            st.dataframe(pac, use_container_width=True)
        except Exception as e:
            st.error(f"خطأ في التقارير: {e}")
    else:
        st.info("لا توجد بيانات حتى الآن")

with tab4:
    st.subheader("📜 السجل الكامل")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("السجل فارغ")
