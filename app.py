import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa - الوضع الليلي", layout="wide")

# رابط الصورة التي رفعتها
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# تنسيق الوضع الليلي (Dark Mode)
st.markdown(f"""
    <style>
    /* جعل الخلفية داكنة مع اللوجو */
    .stApp {{
        background-color: #0e1117; /* لون أسود مريح */
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("{logo_path}");
        background-attachment: fixed;
        background-size: 350px;
        background-position: center;
        background-repeat: no-repeat;
    }}
    
    /* تنسيق النصوص لتناسب الوضع الليلي */
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3 {{ color: #4caf50 !important; text-align: right; }} /* أخضر فاتح للعناوين */
    p, span, label {{ color: #ffffff !important; text-align: right; }} /* أبيض للنصوص */
    
    /* تنسيق الجدول في الوضع الليلي */
    div[data-testid="stDataFrame"] {{
        background-color: #161b22;
        border-radius: 10px;
    }}

    /* تنسيق الأزرار (أزرق Sympa) */
    div.stButton > button {{ 
        width: 100%; 
        border-radius: 20px; 
        background-color: #00a4e4; 
        color: white; 
        font-weight: bold;
        border: none;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}

    /* القائمة الجانبية الداكنة */
    section[data-testid="stSidebar"] {{
        background-color: #161b22 !important;
        direction: rtl;
    }}
    
    /* تحسين خانات الإدخال */
    input {{
        background-color: #0d1117 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- نظام كلمة السر ---
st.sidebar.image(logo_path, width=150)
st.sidebar.title("🔐 دخول الإدارة")
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password != "2025":
    st.title("🌙 نظام Bébé Sympa الليلي")
    st.warning("يرجى إدخال كلمة السر (2025) في القائمة الجانبية.")
    st.stop()

# --- محتوى التطبيق ---
st.title("📊 لوحة الإنتاج - Bébé Sympa")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
    df.columns = df.columns.str.strip()
except:
    df = pd.DataFrame()

if not df.empty:
    st.header("🔎 البحث عن طلبية")
    search_query = st.text_input("ابحث عن منتج أو ورشة (اكتب هنا):")
    
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
            # فلترة ذكية لعدد الطلبات قيد الخياطة
            in_progress = len(df[df['الحالة'].str.contains('خياطة', na=False)])
            st.metric("🧵 قيد الخياطة", in_progress)
else:
    st.info("لا توجد بيانات حالياً في جدول جوجل.")
