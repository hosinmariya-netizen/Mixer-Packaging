import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="نظام تتبع الورش المتقدم", layout="wide")

st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🧵 نظام تتبع الإنتاج - مرتبط بجوجل")

# إنشاء الاتصال
conn = st.connection("gsheets", type=GSheetsConnection)

# قراءة البيانات
try:
    df = conn.read(ttl="0")
except:
    df = pd.DataFrame(columns=["المنتج", "ورشة_الخياطة", "تاريخ_الخروج_للخياطة", "ورشة_التغليف", "تاريخ_الخروج_للتغليف", "الحالة"])

# القائمة الجانبية
st.sidebar.header("➕ إضافة عمل جديد")
with st.sidebar.form("add_form", clear_on_submit=True):
    order_name = st.text_input("اسم المنتج")
    sewing_ws = st.text_input("اسم ورشة الخياطة")
    submit = st.form_submit_button("تسجيل خروج للخياطة")

    if submit and order_name and sewing_ws:
        new_row = pd.DataFrame([{
            "المنتج": order_name,
            "ورشة_الخياطة": sewing_ws,
            "تاريخ_الخروج_للخياطة": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "الحالة": "في الخياطة"
        }])
        df = pd.concat([df, new_row], ignore_index=True).fillna("-")
        conn.update(data=df)
        st.success("تم التحديث في جوجل!")
        st.rerun()

# عرض البيانات وتحديثها
st.header("📊 حالة العمل الحالية")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    st.divider()
    st.subheader("🔄 تحديث مرحلة المنتج")
    order_to_update = st.selectbox("اختر المنتج لتحديثه", df[df["الحالة"]=="في الخياطة"]["المنتج"].unique() if "الحالة" in df.columns else [])
    packaging_ws = st.text_input("اسم ورشة التغليف")
    
    if st.button("تحويل للتغليف"):
        if order_to_update and packaging_ws:
            idx = df[df["المنتج"] == order_to_update].index[-1]
            df.at[idx, "ورشة_التغليف"] = packaging_ws
            df.at[idx, "تاريخ_الخروج_للتغليف"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            df.at[idx, "الحالة"] = "في التغليف"
            conn.update(data=df)
            st.success(f"تم تحويل {order_to_update} للتغليف")
            st.rerun()
else:
    st.info("لا توجد بيانات مسجلة حالياً في جدول جوجل.")
