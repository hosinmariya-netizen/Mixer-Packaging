import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# 2. الربط بجوجل شيت (استخدام Secrets المرفوعة على Streamlit)
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        # الرابط الخاص بملفك
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بجوجل: {e}")
        return None

# 3. جلب البيانات وتنظيفها
def load_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # التأكد من وجود الأعمدة الأساسية
        cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
        for c in cols:
            if c not in df.columns: df[c] = ""
        # تحويل الكمية لرقم
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

# إدارة تحديث البيانات
if "df" not in st.session_state:
    st.session_state.df = load_data()

# 4. الواجهة والتبويبات
st.title("🛡️ نظام الرقابة المطور - Bébé Sympa")

tabs = st.tabs(["📥 استلام بضاعة", "📤 إخراج بضاعة", "🏢 جرد المخزن", "📜 السجل"])

# --- تبويب الاستلام ---
with tabs[0]:
    st.subheader("تسجيل دخول بضاعة من المنازل")
    with st.form("in_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        f_home = col1.text_input("اسم المنزل")
        f_prod = col2.text_input("اسم المنتج")
        f_qty = col3.number_input("الكمية", min_value=1)
        
        if st.form_submit_button("✅ تأكيد الحفظ"):
            if f_home and f_prod and f_qty > 0:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                get_sheet().append_row([f_qty, f_prod, f_home, now, "st"])
                st.success("تم تسجيل البيانات بنجاح!")
                st.session_state.df = load_data() # تحديث البيانات فوراً
                st.rerun()

# --- تبويب المخزن (الحسابات الذكية) ---
with tabs[2]:
    st.subheader("🏢 حالة المخزن الحالية")
    df = st.session_state.df
    if not df.empty:
        # حساب الداخل (st) والخارج (ct, fn)
        summary_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        summary_out = df[df['الحالة'].isin(['ct', 'fn'])].groupby('المنتج')['الكمية'].sum()
        
        # الرصيد = الداخل - الخارج
        inventory = (summary_in - summary_out).fillna(summary_in).reset_index()
        inventory.columns = ['المنتج', 'الرصيد المتاح']
        
        # عرض بطاقات سريعة
        st.dataframe(inventory, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات لعرضها")

