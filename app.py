import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة وتثبيت الرأس البرتقالي (CSS)
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* منع التفاف العناصر وإجبارها على العرض الأفقي */
    .table-container {
        overflow-x: auto;
        max-height: 550px;
        border: 1px solid #444;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        min-width: 800px; /* لضمان بقاء الجدول عريضاً */
        table-layout: fixed;
    }
    
    /* تثبيت الرأس البرتقالي */
    th {
        position: sticky;
        top: 0;
        background-color: #ffa500 !important;
        color: black !important;
        z-index: 100;
        border: 1px solid #444;
        padding: 12px;
        font-weight: bold;
    }
    
    td {
        border: 1px solid #444;
        padding: 5px;
        text-align: center;
        vertical-align: middle;
        overflow: hidden;
    }
    
    .row-even { background-color: #D6C1A6; color: black; }
    .row-odd { background-color: #1e2124; color: white; }
    
    /* تنسيق زر التصفير ليكون صغيراً */
    .stButton>button { width: 100%; padding: 2px; height: 35px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الربط بـ Google Sheets
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except: return None

def get_data():
    s = get_sheet()
    if s:
        df = pd.DataFrame(s.get_all_records())
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

def update_val(row_idx, col_name, val):
    s = get_sheet()
    if s:
        # البحث عن رقم العمود بالاسم
        headers = s.row_values(1)
        col_idx = headers.index(col_name) + 1
        s.update_cell(row_idx + 2, col_idx, val)

# 3. واجهة المستخدم
try:
    df = get_data()
    if not df.empty:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    st.title("🛡️ الرقابة الذكية - Bébé Sympa")
    
    t = st.tabs(["🏠 العمليات", "🏢 المخزن", "📜 History"])

    with t[2]:
        st.subheader("سجل العمليات (Excel Style)")
        if not df.empty:
            # عرض آخر 50 عملية (الأحدث فوق)
            recent = df.tail(50).iloc[::-1]
            
            # بناء هيكل الجدول
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            
            # رأس الجدول الثابت
            h_cols = st.columns([0.8, 1.2, 1, 1.2, 1.5, 2])
            h_labels = ["تصفير", "الكمية", "الحالة", "المنتج", "المنزل", "التاريخ"]
            for col, label in zip(h_cols, h_labels):
                col.markdown(f'<div style="background:#ffa500; color:black; padding:10px; border:1px solid #444; text-align:center; font-weight:bold;">{label}</div>', unsafe_allow_html=True)
            
            # صفوف الجدول
            for i, row in recent.iterrows():
                bg = "#D6C1A6" if i % 2 == 0 else "#1e2124"
                tc = "black" if i % 2 == 0 else "white"
                
                # استخدام columns داخل الـ حاوية لضمان العرض الأفقي
                r_cols = st.columns([0.8, 1.2, 1, 1.2, 1.5, 2])
                
                # 1. زر التصفير
                with r_cols[0]:
                    if st.button("❌", key=f"z_{i}"):
                        update_val(i, 'الكمية', 0)
                        st.cache_resource.clear()
                        st.rerun()
                
                # 2. تعديل الكمية
                with r_cols[1]:
                    new_q = st.number_input("", value=int(row['الكمية']), key=f"q_{i}", label_visibility="collapsed")
                    if new_q != int(row['الكمية']):
                        update_val(i, 'الكمية', new_q)
                        st.cache_resource.clear()
                        st.rerun()
                
                # 3. بقية البيانات (أفقية)
                r_cols[2].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:40px; display:flex; align-items:center; justify-content:center;">{row["الحالة"]}</div>', unsafe_allow_html=True)
                r_cols[3].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:40px; display:flex; align-items:center; justify-content:center;">{row["المنتج"]}</div>', unsafe_allow_html=True)
                r_cols[4].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:40px; display:flex; align-items:center; justify-content:center;">{row["المنزل"]}</div>', unsafe_allow_html=True)
                
                # تاريخ سطرين
                d = row["التاريخ"].replace(" ", "<br>")
                r_cols[5].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:40px; font-size:11px; display:flex; align-items:center; justify-content:center; text-align:center;">{d}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات سجل.")

except Exception as e:
    st.error(f"خطأ: {e}")
                    
