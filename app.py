import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa للإنتاج", layout="wide")

# رابط الصورة التي رفعتها أنت على GitHub
# قمت بتعديل الروابط لتناسب الملف الذي رفعته (images (5) (5).jpeg)
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# تنسيق الألوان والشعار في الخلفية
st.markdown(f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(255,255,255,0.94), rgba(255,255,255,0.94)), url("{logo_path}");
        background-attachment: fixed;
        background-size: 300px; /* حجم اللوجو في الخلفية */
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p {{ color: #2e7d32; text-align: right; }}
    
    div.stButton > button {{ 
        width: 100%; 
        border-radius: 20px; 
        background-color: #00a4e4; 
        color: white; 
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- نظام كلمة السر ---
st.sidebar.image(logo_path, width=150)
st.sidebar.title("🔐 دخول الإدارة")
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password != "2025":
    st.title("🧵 مرحباً بك في Bébé Sympa")
    st.warning("يرجى إدخل كلمة السر في القائمة الجانبية (2025)")
    st.stop()

# --- محتوى التطبيق ---
st.title("📊 لوحة مراقبة الإنتاج - Bébé Sympa")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
    df.columns = df.columns.str.strip()
except:
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
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.metric("📦 إجمالي الطلبيات", len(df))
    with c2:
        if 'الحالة' in df.columns:
            in_progress = len(df[df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("🧵 قيد الخياطة", in_progress)
            
