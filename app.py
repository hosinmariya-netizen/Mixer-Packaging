import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

st.set_page_config(page_title="نظام تتبع الورش", layout="wide")

# تنسيق الواجهة والخطوط
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #28a745; color: white; font-weight: bold; }
    input { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 نظام مراقبة الإنتاج والبحث")

# ربط جوجل شيت
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
except Exception as e:
    st.error("تأكد من إعداد Secrets بشكل صحيح")
    df = pd.DataFrame(columns=["المنتج", "ورشة_الخياطة", "تاريخ_الخروج_للخياطة", "ورشة_التغليف", "تاريخ_الخروج_للتغليف", "الحالة"])

# --- قسم البحث (الجديد) ---
st.header("🔎 البحث عن طلبية")
search_query = st.text_input("ادخل اسم المنتج أو اسم الورشة للبحث:")

# تصفية البيانات بناءً على البحث
if search_query:
    filtered_df = df[
        df['المنتج'].astype(str).str.contains(search_query, na=False) | 
        df['ورشة_الخياطة'].astype(str).str.contains(search_query, na=False)
    ]
else:
    filtered_df = df

# عرض النتائج
if not filtered_df.empty:
    st.success(f"تم العثور على {len(filtered_df)} نتيجة")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("لا توجد نتائج مطابقة للبحث.")

st.divider()

# --- القائمة الجانبية للإضافة (اختيارية إذا كنت تريد الإضافة من التطبيق) ---
with st.sidebar:
    st.header("📝 إضافة سريعة")
    with st.form("add_form", clear_on_submit=True):
        order_name = st.text_input("اسم المنتج الجديد")
        sewing_ws = st.text_input("ورشة الخياطة")
        submit = st.form_submit_button("إرسال إلى جوجل شيت")

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
            st.success("تم التحديث!")
            st.rerun()

st.info("💡 يمكنك دائماً تعديل البيانات مباشرة من ملف Google Sheets وسوف تظهر هنا فوراً.")
