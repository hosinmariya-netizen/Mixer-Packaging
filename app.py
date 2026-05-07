import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="نظام تتبع الورش", layout="wide")

# تصحيح الخطأ هنا (استخدام unsafe_allow_html بدلا من stdio)
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 نظام تتبع الإنتاج - مرتبط بجوجل")

# إنشاء الاتصال بجوجل شيت
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
except Exception as e:
    st.error("تأكد من إعداد Secrets بشكل صحيح في Streamlit")
    df = pd.DataFrame(columns=["المنتج", "ورشة_الخياطة", "تاريخ_الخروج_للخياطة", "ورشة_التغليف", "تاريخ_الخروج_للتغليف", "الحالة"])

# القائمة الجانبية للإضافة
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
            "ورشة_التغليف": "-",
            "تاريخ_الخروج_للتغليف": "-",
            "الحالة": "في الخياطة"
        }])
        df = pd.concat([df, new_row], ignore_index=True).fillna("-")
        conn.update(data=df)
        st.success("تم الحفظ في جوجل!")
        st.rerun()

# عرض البيانات
st.header("📊 حالة العمل الحالية")
st.dataframe(df, use_container_width=True)

# تحديث البيانات
if not df.empty and "الحالة" in df.columns:
    st.divider()
    st.subheader("🔄 تحويل إلى التغليف")
    undelivered = df[df["الحالة"] == "في الخياطة"]["المنتج"].unique()
    if len(undelivered) > 0:
        order_to_update = st.selectbox("اختر المنتج", undelivered)
        packaging_ws = st.text_input("اسم ورشة التغليف")
        if st.button("تأكيد التحويل"):
            idx = df[df["المنتج"] == order_to_update].index[-1]
            df.at[idx, "ورشة_التغليف"] = packaging_ws
            df.at[idx, "تاريخ_الخروج_للتغليف"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            df.at[idx, "الحالة"] = "تم التغليف"
            conn.update(data=df)
            st.success("تم التحديث!")
            st.rerun()
            
