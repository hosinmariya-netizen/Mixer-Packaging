import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa - تحديث فوري", layout="wide")

# رابط الصورة التي رفعتها
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# تنسيق الوضع الليلي (Dark Mode)
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("{logo_path}");
        background-attachment: fixed;
        background-size: 350px;
        background-position: center;
        background-repeat: no-repeat;
    }}
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3 {{ color: #4caf50 !important; text-align: right; }}
    p, span, label {{ color: #ffffff !important; text-align: right; }}
    div.stButton > button {{ 
        width: 100%; 
        border-radius: 20px; 
        background-color: #00a4e4; 
        color: white; 
        font-weight: bold;
    }}
    /* تنسيق خاص لزر التحديث ليبرز */
    .refresh-btn > div > button {{
        background-color: #28a745 !important;
        border-radius: 10px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- نظام كلمة السر ---
st.sidebar.image(logo_path, width=150)
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password != "2025":
    st.title("🌙 نظام Bébé Sympa")
    st.warning("يرجى إدخال كلمة السر (2025)")
    st.stop()

# --- محتوى التطبيق ---
# إنشاء صفين للعنوان وزر التحديث
col_title, col_refresh = st.columns([4, 1])

with col_title:
    st.title("📊 لوحة الإنتاج المباشرة")

with col_refresh:
    st.write("##") # لإزاحة الزر لأسفل قليلاً ليحاذي العنوان
    if st.button("🔄 تحديث البيانات"):
        st.cache_data.clear() # مسح الذاكرة المؤقتة
        st.rerun() # إعادة تشغيل الكود لجلب البيانات الجديدة

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # تعديل: أضفنا ttl=0 لضمان عدم تخزين البيانات القديمة
    df = conn.read(ttl=0) 
    df.columns = df.columns.str.strip()
except:
    st.error("فشل الاتصال بجوجل شيت")
    df = pd.DataFrame()

if not df.empty:
    st.header("🔎 البحث")
    search_query = st.text_input("ابحث عن منتج أو ورشة:")
    
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, na=False)).any(axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.metric("📦 إجمالي الطلبيات", len(df))
    with c2:
        if 'الحالة' in df.columns:
            in_progress = len(df[df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("🧵 قيد الخياطة", in_progress)
else:
    st.info("الجدول فارغ حالياً.")
    
