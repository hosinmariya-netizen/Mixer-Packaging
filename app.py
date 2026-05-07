import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa للإنتاج", layout="wide")

# رابط اللوجو الخاص بك (تم رفعه ليظهر في الخلفية)
logo_url = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/logo.png" 

# إضافة اللوجو في الخلفية وتنسيق الألوان بناءً على شعار Bébé Sympa
st.markdown(f"""
    <style>
    /* خلفية اللوجو الشفافة */
    .stApp {{
        background-image: linear-gradient(rgba(255,255,255,0.92), rgba(255,255,255,0.92)), url("https://i.ibb.co/Vp884Y7/image.png");
        background-attachment: fixed;
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* تنسيق النصوص والاتجاه */
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p {{ color: #2e7d32; text-align: right; }} /* لون أخضر مثل اللوجو */
    
    /* تنسيق الأزرار باللون الأزرق الجذاب من اللوجو */
    div.stButton > button {{ 
        width: 100%; 
        border-radius: 20px; 
        background-color: #00a4e4; 
        color: white; 
        font-weight: bold;
        border: none;
    }}
    
    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {{
        background-color: #f1f8e9;
        direction: rtl;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- نظام كلمة السر ---
st.sidebar.image("https://i.ibb.co/Vp884Y7/image.png", width=150)
st.sidebar.title("🔐 دخول الإدارة")
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password != "2025":
    st.title("🧵 مرحباً بك في Bébé Sympa")
    st.warning("يرجى إدخال كلمة السر في القائمة الجانبية لرؤية جدول الإنتاج.")
    st.stop()

# --- محتوى التطبيق بعد كلمة السر ---
st.title("📊 لوحة مراقبة الإنتاج - Bébé Sympa")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error("خطأ في الاتصال بجوجل شيت")
    df = pd.DataFrame()

if not df.empty:
    st.header("🔎 البحث عن طلبية")
    search_query = st.text_input("ابحث عن منتج أو ورشة:")
    
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, na=False)).any(axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)
    
    # الإحصائيات بألوان جميلة
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
    
