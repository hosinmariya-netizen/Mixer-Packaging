import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
# نظام حماية بسيط بكلمة سر
password = st.sidebar.text_input("أدخل كلمة السر لرؤية البيانات", type="password")
if password != "1234": # يمكنك تغيير 1234 لأي رقم تريده
    st.warning("يرجى إدخال كلمة السر الصحيحة في القائمة الجانبية")
    st.stop() # يمنع ظهور باقي الموقع إذا كانت الكلمة خطأ
    
st.set_page_config(page_title="نظام تتبع الورش", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #28a745; color: white; }
    input { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 نظام مراقبة الإنتاج والبحث")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
    
    # تنظيف أسماء الأعمدة من المسافات الزائدة (حل مشكلة KeyError)
    df.columns = df.columns.str.strip()
    
except Exception as e:
    st.error("هناك مشكلة في قراءة البيانات من جوجل. تأكد من وجود عناوين في السطر الأول.")
    df = pd.DataFrame()

# التأكد من وجود أعمدة قبل البحث
if not df.empty:
    st.header("🔎 البحث عن طلبية")
    search_query = st.text_input("ادخل اسم المنتج أو اسم الورشة للبحث:")

    # البحث في كل الأعمدة لتجنب الأخطاء
    if search_query:
        # يبحث في كل سطر إذا كان النص موجوداً في أي خانة
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, na=False)).any(axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("لا توجد نتائج مطابقة.")
else:
    st.info("الجدول فارغ حالياً. قم بإضافة بيانات في ملف Google Sheets.")

# زر الإحصائيات (الذي اقترحته لك)
if not df.empty:
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("إجمالي الطلبيات", len(df))
    with col2:
        if 'الحالة' in df.columns:
            in_progress = len(df[df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("طلبيات قيد الخياطة", in_progress)
            
