import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام تتبع الورش المحمي", layout="wide")

# تنسيق الواجهة
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #28a745; color: white; }
    input { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- نظام كلمة السر ---
st.sidebar.title("🔐 تسجيل الدخول")
user_password = st.sidebar.text_input("أدخل كلمة السر لرؤية البيانات", type="password")

# كلمة السر هي 2025
if user_password != "2025":
    st.title("🔒 موقع محمي")
    st.warning("يرجى إدخال كلمة السر في القائمة الجانبية لتتمكن من رؤية جدول الكميات والبحث.")
    st.info("إذا كنت المالك، ادخل الكلمة التي حددناها مسبقاً.")
    st.stop() # توقف الكود هنا ولا يظهر باقي المحتوى

# --- باقي التطبيق (لا يظهر إلا بعد كلمة السر) ---
st.title("🔍 نظام مراقبة الإنتاج والبحث")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error("مشكلة في الاتصال بجوجل شيت")
    df = pd.DataFrame()

if not df.empty:
    st.header("🔎 البحث عن طلبية")
    search_query = st.text_input("ادخل اسم المنتج أو اسم الورشة للبحث:")
    
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, na=False)).any(axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    # الإحصائيات
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي الطلبيات", len(df))
    with col2:
        if 'الحالة' in df.columns:
            in_progress = len(df[df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("طلبيات قيد الخياطة", in_progress)
else:
    st.info("الجدول فارغ حالياً.")
    
