import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

st.set_page_config(page_title="نظام الورشة - خياطة وتغليف", layout="wide", page_icon="🧵")

# تنسيقات
st.markdown("""
    <style>
    .stApp { direction: rtl; }
    .stButton>button { background-color: #4CAF50; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# اتصال Google Sheet
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

def get_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        cols = ["المنتج", "الكمية", "منزل_الخياطة", "منزل_التغليف", "التاريخ", "المرحلة", "ملاحظات"]
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

def safe_int(v):
    try:
        return int(float(v)) if pd.notna(v) else 0
    except:
        return 0

# بيانات الجلسة
if "df" not in st.session_state:
    st.session_state.df = get_data()
df = st.session_state.df

# عناوين
st.title("🧵 نظام متابعة الخياطة والتغليف")
st.caption("تسجيل المنتجات مع منزل الخياطة ومنزل التغليف")

col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.session_state.df = get_data()
        st.rerun()

# قوائم المنازل والمنتجات من البيانات
def get_all_homes():
    homes = set()
    if not df.empty:
        homes.update(df['منزل_الخياطة'].dropna().unique())
        homes.update(df['منزل_التغليف'].dropna().unique())
    return [h for h in homes if h and h not in ["-", ""]]

def get_all_products():
    if not df.empty:
        return [p for p in df['المنتج'].dropna().unique() if p and p not in ["-", ""]]
    return []

homes_list = get_all_homes()
products_list = get_all_products()

# ===================== تبويبات =====================
tabs = st.tabs(["📥 تسجيل خياطة", "📦 تسجيل تغليف", "📊 المخزون والتقرير", "📜 السجل", "🏁 إنجاز"])

# ----- تبويب 1: تسجيل خياطة -----
with tabs[0]:
    st.subheader("🧵 تسجيل عملية خياطة")
    with st.form("sewing_form"):
        col1, col2, col3 = st.columns(3)
        product = col1.selectbox("المنتج", options=products_list if products_list else ["أضف منتجاً أولاً"])
        qty = col2.number_input("الكمية المخيطة", min_value=1, step=1)
        home = col3.selectbox("منزل الخياطة", options=homes_list if homes_list else ["أضف منزلاً أولاً"])
        notes = st.text_input("ملاحظات (اختياري)")
        new_product = st.text_input("أو أدخل منتج جديد")
        new_home = st.text_input("أو أدخل منزل خياطة جديد")

        if st.form_submit_button("✅ تسجيل الخياطة"):
            final_product = new_product.strip() if new_product.strip() else product
            final_home = new_home.strip() if new_home.strip() else home
            if qty > 0 and final_product and final_home:
                append_row([final_product, qty, final_home, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "خياطة", notes])
                st.cache_resource.clear()
                st.session_state.df = get_data()
                st.success(f"تم تسجيل {qty} من {final_product} لخياطة في {final_home}")
                st.rerun()
            else:
                st.warning("البيانات ناقصة")

# ----- تبويب 2: تسجيل تغليف -----
with tabs[1]:
    st.subheader("📦 تسجيل عملية تغليف")
    with st.form("packing_form"):
        col1, col2, col3 = st.columns(3)
        product = col1.selectbox("المنتج", options=products_list if products_list else ["أضف منتجاً أولاً"])
        qty = col2.number_input("الكمية المغلفة", min_value=1, step=1)
        home = col3.selectbox("منزل التغليف", options=homes_list if homes_list else ["أدخل منزلاً"])
        notes = st.text_input("ملاحظات (اختياري)")
        new_product = st.text_input("أو أدخل منتج جديد")
        new_home = st.text_input("أو أدخل منزل تغليف جديد")

        if st.form_submit_button("✅ تسجيل التغليف"):
            final_product = new_product.strip() if new_product.strip() else product
            final_home = new_home.strip() if new_home.strip() else home
            if qty > 0 and final_product and final_home:
                append_row([final_product, qty, "", final_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "تغليف", notes])
                st.cache_resource.clear()
                st.session_state.df = get_data()
                st.success(f"تم تسجيل {qty} من {final_product} لتغليف في {final_home}")
                st.rerun()
            else:
                st.warning("البيانات ناقصة")

# ----- تبويب 3: المخزون والتقرير -----
with tabs[2]:
    st.subheader("📊 ملخص المنتجات حسب المنازل")
    if not df.empty:
        # تجميع كميات الخياطة لكل منتج وكل منزل خياطة
        sewing = df[df['المرحلة'] == 'خياطة'].groupby(['المنتج', 'منزل_الخياطة'])['الكمية'].sum().reset_index()
        sewing.columns = ['المنتج', 'منزل الخياطة', 'كمية خياطة']

        # تجميع كميات التغليف لكل منتج وكل منزل تغليف
        packing = df[df['المرحلة'] == 'تغليف'].groupby(['المنتج', 'منزل_التغليف'])['الكمية'].sum().reset_index()
        packing.columns = ['المنتج', 'منزل التغليف', 'كمية تغليف']

        # عرض الجدولين بشكل منفصل
        st.markdown("### خياطة حسب المنتج والمنزل")
        st.dataframe(sewing, use_container_width=True, hide_index=True)

        st.markdown("### تغليف حسب المنتج والمنزل")
        st.dataframe(packing, use_container_width=True, hide_index=True)

        # إجماليات
        total_sewing = sewing['كمية خياطة'].sum()
        total_packing = packing['كمية تغليف'].sum()
        col1, col2 = st.columns(2)
        col1.metric("🧵 إجمالي الخياطة", safe_int(total_sewing))
        col2.metric("📦 إجمالي التغليف", safe_int(total_packing))

        # تحذير إذا كان التغليف أكبر من الخياطة
        if total_packing > total_sewing:
            st.warning("⚠️ كميات التغليف أكبر من الخياطة! تأكد من التسجيلات.")
    else:
        st.info("لا توجد بيانات")

# ----- تبويب 4: السجل -----
with tabs[3]:
    st.subheader("📜 سجل العمليات")
    if not df.empty:
        log = df.copy()
        log = log.iloc[::-1]
        log['الكمية'] = log['الكمية'].apply(safe_int)
        log['التاريخ'] = pd.to_datetime(log['التاريخ'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(log, use_container_width=True)
        csv = log.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل CSV", csv, f"log_{datetime.datetime.now():%Y%m%d_%H%M}.csv", "text/csv")
    else:
        st.info("لا توجد سجلات")

# ----- تبويب 5: إنجاز (حسب المنزل) -----
with tabs[4]:
    st.subheader("✅ إنجاز كل منزل (الكمية المنفذة)")
    if not df.empty:
        # أداء منازل الخياطة
        sewing_perf = df[df['المرحلة'] == 'خياطة'].groupby('منزل_الخياطة')['الكمية'].sum().reset_index()
        sewing_perf.columns = ['منزل الخياطة', 'إجمالي خياطة']
        # أداء منازل التغليف
        packing_perf = df[df['المرحلة'] == 'تغليف'].groupby('منزل_التغليف')['الكمية'].sum().reset_index()
        packing_perf.columns = ['منزل التغليف', 'إجمالي تغليف']

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### منازل الخياطة")
            st.dataframe(sewing_perf, use_container_width=True, hide_index=True)
        with col2:
            st.markdown("#### منازل التغليف")
            st.dataframe(packing_perf, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات")
