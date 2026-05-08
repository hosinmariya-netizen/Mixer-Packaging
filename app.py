import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق الجمالي (الصورة الشفافة)
st.set_page_config(page_title="Bébé Sympa - نظام الورشة", layout="wide", page_icon="🧵")

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
    .stButton>button { border-radius: 8px; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بجوجل شيت
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
        expected_cols = ["الكمية", "المنتج", "العميل", "منزل_الخياطة", "منزل_التغليف", "التاريخ", "المرحلة"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

def safe_int(value):
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except:
        return 0

def get_unique_values(df, column):
    if not df.empty and column in df.columns:
        return [v for v in df[column].unique() if v and v not in ["", "-"]]
    return []

# 3. الواجهة الرئيسية
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    # الهيدر وتحديث
    st.title("🧵 نظام إدارة الورشة - Bébé Sympa")
    st.caption("تسجيل عمليات الخياطة (CT) والتغليف (FN) مع تحديد المنزل المنفذ")
    if st.button("🔄 تحديث البيانات"):
        st.cache_resource.clear()
        st.session_state.df = get_data()
        st.rerun()

    # إحصائيات سريعة
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("📊 إجمالي المعاملات", len(df))
        with col2: st.metric("👥 العملاء", len(get_unique_values(df, "العميل")))
        with col3: st.metric("📦 المنتجات", len(get_unique_values(df, "المنتج")))
        with col4: st.metric("📈 إجمالي الكميات", safe_int(df['الكمية'].sum()))

    # التبويبات
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👥 العملاء", "🧵 خياطة CT", "📦 تغليف FN", "📊 التقارير", "📜 السجل", "✅ الإنجاز"])

    # --- العملاء ---
    with tab1:
        st.subheader("👥 إدارة العملاء")
        clients = get_unique_values(df, "العميل")
        if clients:
            st.write("**قائمة العملاء:**")
            for c in clients: st.write(f"- {c}")
        else:
            st.info("لا يوجد عملاء بعد")
        with st.form("add_client"):
            new_client = st.text_input("اسم عميل جديد")
            if st.form_submit_button("إضافة عميل"):
                if new_client.strip():
                    append_row([0, "", new_client, "", "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "عميل"])
                    st.session_state.df = get_data()
                    st.success(f"تمت إضافة {new_client}")
                    st.rerun()

    # --- خياطة ---
    with tab2:
        st.subheader("🧵 تسجيل خياطة (CT)")
        with st.form("sewing"):
            clients = get_unique_values(df, "العميل")
            products = get_unique_values(df, "المنتج")
            sewing_homes = get_unique_values(df, "منزل_الخياطة")
            col1, col2, col3, col4 = st.columns(4)
            client = col1.selectbox("العميل", clients if clients else ["لا توجد بيانات"])
            product = col2.selectbox("المنتج", products if products else ["لا توجد بيانات"])
            qty = col3.number_input("الكمية", min_value=1, step=1)
            home = col4.selectbox("منزل الخياطة", sewing_homes if sewing_homes else ["لا توجد بيانات"])
            new_client = st.text_input("عميل جديد (اختياري)")
            new_product = st.text_input("منتج جديد (اختياري)")
            new_home = st.text_input("منزل خياطة جديد (اختياري)")
            if st.form_submit_button("تسجيل الخياطة"):
                final_client = new_client.strip() or client
                final_product = new_product.strip() or product
                final_home = new_home.strip() or home
                if qty>0 and final_client and final_product and final_home and "لا توجد بيانات" not in [final_client,final_product,final_home]:
                    append_row([qty, final_product, final_client, final_home, "", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "خياطة"])
                    st.session_state.df = get_data()
                    st.success(f"تم تسجيل {qty} من {final_product} للعميل {final_client} في خياطة {final_home}")
                    st.rerun()
                else: st.warning("املأ جميع الحقول")

    # --- تغليف ---
    with tab3:
        st.subheader("📦 تسجيل تغليف (FN)")
        with st.form("packing"):
            clients = get_unique_values(df, "العميل")
            products = get_unique_values(df, "المنتج")
            packing_homes = get_unique_values(df, "منزل_التغليف")
            col1, col2, col3, col4 = st.columns(4)
            client = col1.selectbox("العميل", clients if clients else ["لا توجد بيانات"])
            product = col2.selectbox("المنتج", products if products else ["لا توجد بيانات"])
            qty = col3.number_input("الكمية", min_value=1, step=1)
            home = col4.selectbox("منزل التغليف", packing_homes if packing_homes else ["لا توجد بيانات"])
            new_client = st.text_input("عميل جديد (اختياري)")
            new_product = st.text_input("منتج جديد (اختياري)")
            new_home = st.text_input("منزل تغليف جديد (اختياري)")
            if st.form_submit_button("تسجيل التغليف"):
                final_client = new_client.strip() or client
                final_product = new_product.strip() or product
                final_home = new_home.strip() or home
                if qty>0 and final_client and final_product and final_home and "لا توجد بيانات" not in [final_client,final_product,final_home]:
                    append_row([qty, final_product, final_client, "", final_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "تغليف"])
                    st.session_state.df = get_data()
                    st.success(f"تم تسجيل {qty} من {final_product} للعميل {final_client} في تغليف {final_home}")
                    st.rerun()
                else: st.warning("املأ جميع الحقول")

    # --- التقارير ---
    with tab4:
        st.subheader("📊 ملخص الإنتاج")
        if not df.empty:
            sewing_summary = df[df['المرحلة'] == 'خياطة'].groupby(['المنتج','منزل_الخياطة'])['الكمية'].sum().reset_index()
            packing_summary = df[df['المرحلة'] == 'تغليف'].groupby(['المنتج','منزل_التغليف'])['الكمية'].sum().reset_index()
            st.markdown("**خياطة حسب المنتج والمنزل**")
            st.dataframe(sewing_summary, use_container_width=True, hide_index=True)
            st.markdown("**تغليف حسب المنتج والمنزل**")
            st.dataframe(packing_summary, use_container_width=True, hide_index=True)
            total_sewing = safe_int(sewing_summary['الكمية'].sum())
            total_packing = safe_int(packing_summary['الكمية'].sum())
            col1, col2 = st.columns(2)
            col1.metric("🧵 إجمالي الخياطة", total_sewing)
            col2.metric("📦 إجمالي التغليف", total_packing)
        else: st.info("لا توجد بيانات")

    # --- السجل ---
    with tab5:
        st.subheader("📜 سجل العمليات")
        if not df.empty:
            log = df.iloc[::-1].copy()
            log['الكمية'] = log['الكمية'].apply(safe_int)
            log['التاريخ'] = pd.to_datetime(log['التاريخ'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(log, use_container_width=True)
            csv = log.to_csv(index=False).encode('utf-8-sig')
            st.download_button("تحميل CSV", csv, f"log_{datetime.datetime.now():%Y%m%d_%H%M}.csv", "text/csv")
        else: st.info("لا توجد سجلات")

    # --- الإنجاز ---
    with tab6:
        st.subheader("✅ إنجاز المنازل")
        if not df.empty:
            sewing_perf = df[df['المرحلة'] == 'خياطة'].groupby('منزل_الخياطة')['الكمية'].sum().reset_index()
            packing_perf = df[df['المرحلة'] == 'تغليف'].groupby('منزل_التغليف')['الكمية'].sum().reset_index()
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**منازل الخياطة**")
                st.dataframe(sewing_perf, use_container_width=True, hide_index=True)
            with col2:
                st.markdown("**منازل التغليف**")
                st.dataframe(packing_perf, use_container_width=True, hide_index=True)
        else: st.info("لا توجد بيانات")

except Exception as e:
    st.error(f"خطأ: {e}")
