import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق الجمالي
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# إضافة CSS مخصص لتحسين المظهر
st.markdown("""
    <style>
    .stApp { direction: rtl; }
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4b4b4b; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال بجوجل شيت
@st.cache_resource
def get_sheet():
    try:
        # تأكد من إضافة الملف السري في Streamlit Secrets
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        # استبدال الرابط برابط الشيت الخاص بك
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def get_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        if not data: # في حال كان الجدول فارغاً
            return pd.DataFrame(columns=["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"])
        df = pd.DataFrame(data)
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# --- منطق التطبيق الرئيسي ---
if "df" not in st.session_state:
    st.session_state.df = get_data()

df = st.session_state.df

# الهيدر
st.title("🛡️ نظام الرقابة المطور - Bébé Sympa")
if st.button("🔄 تحديث البيانات"):
    st.cache_resource.clear()
    st.session_state.df = get_data()
    st.rerun()

tabs = st.tabs(["🏠 استلام", "📤 إخراج للمنازل", "🏢 المخزن", "💰 كشف حساب", "📜 السجل"])

# --- TAB 1: استلام من المنزل ---
with tabs[0]:
    st.subheader("📥 استلام الإنتاج الجاهز")
    if not df.empty:
        # منطق حساب المتبقي عند المنازل (ما تم إخراجه لهم - ما تم استلامه منهم)
        homes = df[df['المنزل'] != "المخزن"]['المنزل'].unique()
        for home in homes:
            with st.expander(f"🏠 منزل: {home}"):
                home_data = df[df['المنزل'] == home]
                for prod in home_data['المنتج'].unique():
                    p_data = home_data[home_data['المنتج'] == prod]
                    # تم إخراجه للمنزل (ct, fn) - تم استلامه منه (st)
                    rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    
                    if rem > 0:
                        col1, col2 = st.columns([2,1])
                        qty = col1.number_input(f"كمية {prod}", min_value=0, max_value=int(rem), key=f"in_{home}_{prod}")
                        if col2.button("تسجيل استلام", key=f"btn_{home}_{prod}"):
                            append_row([qty, prod, home, datetime.datetime.now().strftime("%Y-%m-%d"), "st"])
                            st.success(f"تم استلام {qty} من {prod}")
                            st.rerun()

# --- TAB 2: إخراج بضاعة للمنازل ---
with tabs[1]:
    st.subheader("📤 توزيع مواد خام/عمل للمنازل")
    with st.form("out_to_home"):
        h_name = st.text_input("اسم المنزل")
        p_name = st.text_input("اسم المنتج")
        qty = st.number_input("الكمية", min_value=1)
        status = st.selectbox("نوع العملية", ["ct (قص)", "fn (خياطة)"])
        if st.form_submit_button("إرسال للمنزل"):
            append_row([qty, p_name, h_name, datetime.datetime.now().strftime("%Y-%m-%d"), status[:2]])
            st.success("تم التسجيل")
            st.rerun()

# --- TAB 3: المخزن الرئيسي ---
with tabs[2]:
    st.subheader("🏢 حالة المخزن الحالي")
    if not df.empty:
        # حساب المتوفر: (ما دخل المخزن 'st') - (ما خرج للبيع 'cl')
        in_stock = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        out_stock = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        current_stock = in_stock.subtract(out_stock, fill_value=0)
        
        cols = st.columns(3)
        for i, (prod, q) in enumerate(current_stock.items()):
            if q > 0:
                cols[i % 3].metric(prod, f"{int(q)} قطعة")

# --- TAB 4 & 5: التقارير ---
with tabs[3]:
    st.subheader("💰 ملخص الكميات")
    if not df.empty:
        pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
        st.table(pivot)

with tabs[4]:
    st.subheader("📜 آخر 20 عملية")
    st.dataframe(df.tail(20), use_container_width=True)
        
