import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa الذكي", layout="wide")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق الليلي (Dark Mode)
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("{logo_path}");
        background-attachment: fixed; background-size: 350px; background-position: center; background-repeat: no-repeat;
    }}
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; text-align: right; }}
    div.stButton > button {{ border-radius: 20px; background-color: #00a4e4; color: white; font-weight: bold; }}
    input {{ text-align: right; direction: rtl; background-color: #161b22 !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# --- القائمة الجانبية ---
st.sidebar.image(logo_path, width=150)
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password == "2025":
    st.sidebar.divider()
    st.sidebar.header("📝 تسجيل طلبية جديدة")
    with st.sidebar.form("new_order"):
        prod_name = st.text_input("اسم المنتج")
        ws_name = st.text_input("ورشة الخياطة")
        submit_order = st.form_submit_button("إرسال وحفظ التاريخ")
        
        if submit_order and prod_name and ws_name:
            existing_data = conn.read(ttl=0)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entry = pd.DataFrame([{
                "المنتج": prod_name,
                "ورشة_الخياطة": ws_name,
                "تاريخ_الخروج_للخياطة": now,
                "الحالة": "في الخياطة"
            }])
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True).fillna("-")
            conn.update(data=updated_df)
            st.sidebar.success("تم التسجيل آلياً!")
            st.rerun()

# --- حماية الموقع ---
if user_password != "2025":
    st.title("🌙 نظام Bébé Sympa")
    st.warning("يرجى إدخال كلمة السر")
    st.stop()

# --- واجهة العرض والبحث ---
col_title, col_refresh = st.columns([4, 1])
with col_title: st.title("📊 لوحة الإنتاج والبحث")
with col_refresh:
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

try:
    # جلب البيانات الأصلية
    original_df = conn.read(ttl=0)
    original_df.columns = original_df.columns.str.strip()
    
    st.header("🔎 البحث عن طلبية")
    search_term = st.text_input("اكتب اسم المنتج أو الورشة هنا للفلترة:")

    # منطق البحث المصلح
    if search_term:
        # نبحث في كل الأعمدة ونفلتر النسخة التي سنعرضها فقط
        mask = original_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        display_df = original_df[mask]
    else:
        display_df = original_df

    # عرض الجدول المفلتر
    st.dataframe(display_df, use_container_width=True)
    
    # الإحصائيات بناءً على البيانات المعروضة
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.metric("📦 عدد النتائج", len(display_df))
    with c2:
        if 'الحالة' in display_df.columns:
            in_progress = len(display_df[display_df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("🧵 قيد الخياطة (في النتائج)", in_progress)

except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
