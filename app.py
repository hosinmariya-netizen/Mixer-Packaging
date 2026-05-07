import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - جرد المخزون", page_icon="🟢", layout="wide")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق العام
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.9)), url("{logo_path}");
        background-attachment: fixed; background-size: 350px; background-position: center; background-repeat: no-repeat;
    }}
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; text-align: right; }}
    div.stButton > button {{ border-radius: 20px; background-color: #00a4e4; color: white; font-weight: bold; }}
    
    /* تنسيق الجدول لجعل الأرقام واضحة */
    .stTable td {{ text-align: center !important; font-size: 18px !important; font-weight: bold !important; }}
    .stTable th {{ text-align: center !important; background-color: #1e293b !important; color: #4caf50 !important; }}
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# --- القائمة الجانبية ---
st.sidebar.image(logo_path, width=150)
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password != "2025":
    st.title("🌙 نظام Bébé Sympa")
    st.info("أدخل كلمة السر للوصول")
    st.stop()

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()
    
    st.title("🏭 لوحة جرد الإنتاج المباشرة")
    
    tab1, tab2 = st.tabs(["📋 جرد المخزون (ct & fn)", "🔍 السجل التفصيلي"])

    with tab1:
        st.subheader("📦 حالة المنتجات الحالية في المصنع")
        
        if 'المنتج' in df.columns and 'الحالة' in df.columns:
            # عملية "التحويل" لإنشاء جدول الجرد
            # نحسب تكرار كل منتج بناءً على حالته
            inventory = df.groupby(['المنتج', 'الحالة']).size().unstack(fill_value=0)
            
            # التأكد من وجود الأعمدة حتى لو لم تكن هناك بيانات لها
            if 'ct' not in inventory.columns: inventory['ct'] = 0
            if 'fn' not in inventory.columns: inventory['fn'] = 0
            
            # إعادة ترتيب الأعمدة وتسميتها بالعربي
            inventory = inventory[['ct', 'fn']]
            inventory.columns = ['الكمية في الخياطة (ct)', 'الكمية في التغليف (fn)']
            
            # إضافة عمود الإجمالي الكلي للمنتج
            inventory['الإجمالي العام'] = inventory['الكمية في الخياطة (ct)'] + inventory['الكمية في التغليف (fn)']
            
            # عرض إحصائيات سريعة ملونة
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("🧵 إجمالي الخياطة", inventory['الكمية في الخياطة (ct)'].sum())
            with c2: st.metric("🎁 إجمالي التغليف", inventory['الكمية في التغليف (fn)'].sum())
            with c3: st.metric("📈 مجموع القطع", inventory['الإجمالي العام'].sum())
            
            st.divider()
            # عرض جدول الجرد النهائي
            st.table(inventory)
        else:
            st.warning("يرجى التأكد من تسمية الأعمدة في Google Sheets بـ 'المنتج' و 'الحالة'")

    with tab2:
        if st.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()
            
        search = st.text_input("ابحث عن حركة معينة...")
        
        def apply_color(row):
            status = str(row['الحالة']).strip().lower()
            if status == 'ct': color = 'background-color: #1e3a8a; color: white'
            elif status == 'fn': color = 'background-color: #7f1d1d; color: white'
            else: color = ''
            return [color] * len(row)

        display_df = df.copy()
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
        
        st.dataframe(display_df.style.apply(apply_color, axis=1), use_container_width=True)

except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
