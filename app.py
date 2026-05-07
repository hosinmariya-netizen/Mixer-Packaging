import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="نظام تتبع الورش - جوجل", layout="wide")
st.title("🧵 نظام تتبع الإنتاج (مرتبط بجوجل)")

# إنشاء الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# قراءة البيانات الحالية
df = conn.read(ttl="0") # ttl=0 لضمان تحديث البيانات فوراً

# القائمة الجانبية للإضافة
st.sidebar.header("إضافة عمل جديد")
order_name = st.sidebar.text_input("اسم المنتج")
sewing_ws = st.sidebar.text_input("ورشة الخياطة")

if st.sidebar.button("تسجيل"):
    if order_name and sewing_ws:
        new_data = pd.DataFrame([{
            "المنتج": order_name,
            "ورشة_الخياطة": sewing_ws,
            "تاريخ_الخروج_للخياطة": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ورشة_التغليف": "-",
            "تاريخ_الخروج_للتغليف": "-",
            "الحالة": "في الخياطة"
        }])
        df = pd.concat([df, new_data], ignore_index=True)
        conn.update(data=df)
        st.sidebar.success("تم الحفظ في جوجل!")
        st.rerun()

# عرض البيانات
st.header("📊 الجدول المباشر من جوجل")
st.dataframe(df)
