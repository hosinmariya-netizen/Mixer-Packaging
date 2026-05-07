import streamlit as st
import pandas as pd
import datetime
import os

# اسم ملف تخزين البيانات
DATA_FILE = "garment_tracking.csv"

# وظيفة لتحميل البيانات من الملف أو إنشاء ملف جديد
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["المنتج", "ورشة_الخياطة", "تاريخ_الخروج_للخياطة", "ورشة_التغليف", "تاريخ_الخروج_للتغليف", "الحالة"])

# وظيفة لحفظ البيانات
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# إعداد واجهة الموقع
st.set_page_config(page_title="نظام تتبع ورش الخياطة", layout="wide")
st.title("🧵 نظام تتبع الإنتاج والورش")

df = load_data()

# القائمة الجانبية لإضافة عمل جديد
st.sidebar.header("إضافة عمل جديد")
order_name = st.sidebar.text_input("اسم المنتج / الطلبية")
sewing_ws = st.sidebar.text_input("اسم ورشة الخياطة")

if st.sidebar.button("تسجيل خروج للخياطة"):
    if order_name and sewing_ws:
        new_entry = {
            "المنتج": order_name,
            "ورشة_الخياطة": sewing_ws,
            "تاريخ_الخروج_للخياطة": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ورشة_التغليف": "قيد الانتظار",
            "تاريخ_الخروج_للتغليف": "-",
            "الحالة": "في الخياطة"
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.sidebar.success("تم التسجيل بنجاح!")
    else:
        st.sidebar.error("يرجى ملء كافة الخانات")

# القسم الرئيسي لتحديث الحالة
st.header("📋 حالة العمل الحالية")
if not df.empty:
    st.table(df)
    
    st.subheader("تحديث المرحلة (تحويل للتغليف)")
    order_to_move = st.selectbox("اختر المنتج الذي عاد من الخياطة:", df[df['الحالة'] == 'في الخياطة']['المنتج'].unique())
    packaging_ws = st.text_input("اسم ورشة التغليف")
    
    if st.button("تحويل إلى التغليف"):
        df.loc[df['المنتج'] == order_to_move, 'ورشة_التغليف'] = packaging_ws
        df.loc[df['المنتج'] == order_to_move, 'تاريخ_الخروج_للتغليف'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        df.loc[df['المنتج'] == order_to_move, 'الحالة'] = "في التغليف"
        save_data(df)
        st.success(f"تم تحويل {order_to_move} لورشة {packaging_ws}")
        st.rerun()
else:
    st.info("لا توجد طلبيات مسجلة حالياً.")
