import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* تحسين شكل الحاوية لتكون مريحة للعين */
    [data-testid="stDataFrame"] { background: #1e2124; border-radius: 10px; border: 1px solid #ffa500; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال بـ Google Sheets
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

# 3. بناء الواجهة
try:
    df = load_data()
    
    st.title("🛡️ الرقابة الذكية")
    
    # أزرار سريعة في الأعلى
    if st.button("🔄 تحديث البيانات"):
        st.cache_resource.clear()
        st.rerun()

    tabs = st.tabs(["📊 الإحصائيات", "📜 السجل (History)"])

    # --- تبويب السجل ---
    with tabs[1]:
        st.subheader("سجل العمليات الأخير")
        if not df.empty:
            # عرض الجدول بشكل أفقي مرن جداً وسلس في السحب
            history_df = df.iloc[::-1].head(50).copy()
            
            # عرض الجدول مع تحكم كامل في عرض الخانات
            st.dataframe(
                history_df,
                use_container_width=True,
                height=450,
                column_config={
                    "المنزل": st.column_config.TextColumn("🏠 المنزل", width="small"),
                    "المنتج": st.column_config.TextColumn("📦 المنتج", width="small"),
                    "الحالة": st.column_config.TextColumn("📍 الحالة", width="small"),
                    "الكمية": st.column_config.NumberColumn("🔢 الكمية", width="small"),
                    "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="medium"),
                },
                hide_index=True
            )
            
            st.markdown("---")
            # قسم التصفير (اضف زر التصفير هنا)
            st.subheader("❌ تصفير عملية من السجل")
            # اختيار السطر المراد تصفيره بناءً على التاريخ والمنزل
            options = history_df.index.tolist()
            def format_label(i):
                r = history_df.loc[i]
                return f"{r['المنزل']} | {r['المنتج']} | {int(r['الكمية'])} قطب"
            
            to_delete = st.selectbox("اختر العملية المراد تصفيرها:", options, format_func=format_label)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("تأكيد التصفير النهائي 🗑️", use_container_width=True):
                    row_data = history_df.loc[to_delete]
                    # التصفير بإضافة سطر معاكس (قاعدة الاستلام)
                    save_entry([row_data['الكمية'], row_data['المنتج'], row_data['المنزل'], 
                               datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                    st.success("تم تصفير العملية وإضافتها كاستلام!")
                    st.rerun()

    # --- تبويب الإحصائيات ---
    with tabs[0]:
        if not df.empty:
            st.write("📈 ملخص الكميات حسب الحالة:")
            summary = df.groupby('الحالة')['الكمية'].sum().reset_index()
            st.table(summary)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
