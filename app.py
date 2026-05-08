import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# التنسيق الجمالي
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }
    .stButton>button { 
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {e}")
        return None

@st.cache_data(ttl=60)
def get_data():
    sheet = get_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)            expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"خطأ في القراءة: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

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

# الواجهة الرئيسية
if "df" not in st.session_state or st.session_state.get("refresh_data", False):
    st.session_state.df = get_data()
    st.session_state.refresh_data = False

df = st.session_state.df

# الهيدر
col_t, col_ref = st.columns([4, 1])
with col_t:
    st.title("🛡️ نظام الرقابة المطور")
    st.caption("نظام إدارة المخزون والعملاء")
with col_ref:
    if st.button("🔄 تحديث", use_container_width=True):
        st.cache_data.clear()
        st.session_state.refresh_data = True
        st.rerun()

# الإحصائيات
if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 إجمالي المعاملات", len(df))
    with col2:
        st.metric("🏠 عدد العملاء", df['المنزل'].nunique())
    with col3:
        st.metric("📦 المنتجات", df['المنتج'].nunique())    with col4:
        st.metric("📈 إجمالي الكميات", int(df['الكمية'].sum()))

# التبويبات
tabs = st.tabs(["📥 دخول", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز"])

# TAB 1: دخول
with tabs[0]:
    st.subheader("📥 دخول بضاعة جديدة")
    with st.form("in_form", clear_on_submit=True):
        clients = [h for h in df['المنزل'].unique() if h and str(h).strip()] if not df.empty else []
        products = [p for p in df['المنتج'].unique() if p and str(p).strip()] if not df.empty else []
        
        f1, f2, f3 = st.columns(3)
        in_home = f1.selectbox("العميل", options=[""] + clients, key="in_home")
        in_product = f2.selectbox("المنتج", options=[""] + products, key="in_product")
        in_qty = f3.number_input("الكمية", min_value=1, key="in_qty")
        new_client = st.text_input("أو عميل جديد (اختياري)")
        
        submitted = st.form_submit_button("✅ تسجيل الدخول", use_container_width=True, type="primary")
        
        if submitted:
            final_client = new_client.strip() if new_client.strip() else in_home
            if in_qty > 0 and in_product and final_client:
                if append_row([in_qty, in_product, final_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"]):
                    st.cache_data.clear()
                    st.session_state.refresh_data = True
                    st.success(f"✅ تم التسجيل بنجاح")
                    st.rerun()
            else:
                st.warning("⚠️ أدخل جميع البيانات")

# TAB 2: إخراج
with tabs[1]:
    st.subheader("📤 إخراج بضاعة")
    with st.form("out_form", clear_on_submit=True):
        clients = [h for h in df['المنزل'].unique() if h and str(h).strip()] if not df.empty else []
        products = [p for p in df['المنتج'].unique() if p and str(p).strip()] if not df.empty else []
        
        f1, f2, f3 = st.columns(3)
        o_h = f1.selectbox("العميل", options=[""] + clients)
        o_p = f2.selectbox("المنتج", options=[""] + products)
        o_q = f3.number_input("الكمية", min_value=1)
        o_s = st.radio("نوع الخروج", ["كامل (ct)", "ناقص (fn)"], horizontal=True)
        o_s_value = "ct" if "كامل" in o_s else "fn"
        
        submitted = st.form_submit_button("✅ تسجيل الخروج", use_container_width=True, type="primary")
        
        if submitted:
            if o_q > 0 and o_p and o_h:                if append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), o_s_value]):
                    st.cache_data.clear()
                    st.session_state.refresh_data = True
                    st.success(f"✅ تم التسجيل بنجاح")
                    st.rerun()
            else:
                st.warning("⚠️ أدخل جميع البيانات")

# TAB 3: المخزن
with tabs[2]:
    st.subheader("🏢 رصيد المخزن")
    if not df.empty:
        s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        s_out = df[df['الحالة'].isin(['ct', 'fn'])].groupby('المنتج')['الكمية'].sum()
        stock = s_in.subtract(s_out, fill_value=0).reset_index()
        stock.columns = ['المنتج', 'الكمية']
        stock['الكمية'] = stock['الكمية'].astype(int)
        
        st.metric("إجمالي الرصيد", int(stock['الكمية'].sum()))
        if not stock.empty:
            st.dataframe(stock[stock['الكمية'] > 0], use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد بيانات")

# TAB 4: كشف حساب
with tabs[3]:
    st.subheader("💰 كشف الحساب")
    if not df.empty:
        pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
        pivot = pivot.rename(columns={'st': 'دخول', 'ct': 'خروج كامل', 'fn': 'خروج ناقص'})
        st.dataframe(pivot.astype(int), use_container_width=True)
    else:
        st.info("لا توجد بيانات")

# TAB 5: History
with tabs[4]:
    st.subheader("📜 السجل (آخر 50)")
    if not df.empty:
        hist = df.iloc[::-1].head(50).copy()
        hist['الكمية'] = hist['الكمية'].astype(int)
        hist['التاريخ'] = pd.to_datetime(hist['التاريخ'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        hist['النوع'] = hist['الحالة'].map({'st': '📥 دخول', 'ct': '📤 خروج كامل', 'fn': '📤 خروج ناقص'})
        st.dataframe(hist[['المنزل', 'المنتج', 'الكمية', 'النوع', 'التاريخ']], use_container_width=True, hide_index=True)
        
        csv = hist.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل CSV", data=csv, file_name=f"history.csv", mime="text/csv")
    else:
        st.info("السجل فارغ")

# TAB 6: إنجازwith tabs[5]:
    st.subheader("✅ إنجاز العملاء")
    if not df.empty:
        summary = df.groupby('المنزل').agg(
            المنتجات=('المنتج', 'nunique'),
            دخول=('الكمية', lambda x: x[df.loc[x.index, 'الحالة'] == 'st'].sum()),
            خروج=('الكمية', lambda x: x[df.loc[x.index, 'الحالة'].isin(['ct', 'fn'])].sum())
        ).reset_index()
        summary['الرصيد'] = (summary['دخول'] - summary['خروج']).astype(int)
        summary.columns = ['العميل', 'المنتجات', 'دخول', 'خروج', 'الرصيد']
        
        st.dataframe(summary, use_container_width=True, hide_index=True)
        
        completed = len(summary[summary['الرصيد'] == 0])
        st.success(f"✅ عملاء منجزون: {completed}")
    else:
        st.info("لا توجد بيانات")
