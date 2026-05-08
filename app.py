import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق الجمالي
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
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
    .stButton>button { 
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover { 
        background-color: #45a049;
    }
    .warning-text { color: #ff4b4b; font-weight: bold; }
    .success-text { color: #4CAF50; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بجوجل شيت مع تحسين الكاش
@st.cache_resource
def get_sheet():
    try:        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

@st.cache_data(ttl=60)  # تحديث البيانات كل 60 ثانية كحد أقصى
def get_data():
    sheet = get_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
            # إضافة الأعمدة الناقصة
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            # تحويل الكمية إلى رقم
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة البيانات: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_clients(df):
    """جلب قائمة العملاء من البيانات الموجودة في الذاكرة"""
    if not df.empty:
        unique_clients = [h for h in df['المنزل'].unique() if pd.notna(h) and str(h).strip() not in ["", "-"]]
        return sorted(unique_clients)
    return []

def append_row(row):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"خطأ في الحفظ: {e}")
            return False
    return False

# 3. الواجهة الرئيسيةtry:
    # تحميل البيانات مرة واحدة وتحديثها عند الحاجة
    if "df" not in st.session_state or st.session_state.get("refresh_data", False):
        st.session_state.df = get_data()
        st.session_state.refresh_data = False
    
    df = st.session_state.df
    clients_list = get_clients(df)

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والعملاء - Bébé Sympa")
    with col_ref:
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.cache_data.clear()
            st.session_state.refresh_data = True
            st.rerun()

    # إحصائيات سريعة
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 إجمالي المعاملات", f"{len(df):,}")
        with col2:
            st.metric("🏠 عدد العملاء", f"{df['المنزل'].nunique():,}")
        with col3:
            st.metric("📦 أنواع المنتجات", f"{df['المنتج'].nunique():,}")
        with col4:
            total_qty = df['الكمية'].sum()
            st.metric("📈 إجمالي الكميات", f"{int(total_qty):,}")

    tabs = st.tabs(["👥 العملاء", "📥 دخول", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز"])

    # --- TAB 0: إدارة العملاء ---
    with tabs[0]:
        st.subheader("👥 إدارة العملاء")
        st.markdown("### 🏠 العملاء المسجلون في النظام")
        if clients_list:
            st.success(f"✅ عدد العملاء النشطين: **{len(clients_list)}**")
            # عرض العملاء في أعمدة لتنظيم العرض
            cols = st.columns(3)
            for idx, client in enumerate(clients_list):
                cols[idx % 3].info(f"👤 {client}")
        else:
            st.info("💡 لا يوجد عملاء في النظام بعد. ابدأ بتسجيل عملية دخول أو خروج لإضافة عميل جديد.")
        
        st.markdown("---")
        st.caption("💡 ملاحظة: يتم إضافة العملاء تلقائياً عند تسجيل أول معاملة
