import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والتصميم
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* حاوية التمرير الأفقي والرأسي */
    .table-viewport {
        overflow-x: auto;
        max-height: 550px;
        border: 1px solid #444;
        background: #1e2124;
    }
    
    /* إجبار الجدول على عرض محدد لضمان السحب الجانبي دون تمطيط */
    .fixed-table {
        min-width: 900px;
        width: 100%;
        border-collapse: collapse;
    }
    
    /* تثبيت الرأس البرتقالي */
    .sticky-header th {
        position: sticky;
        top: 0;
        background-color: #ffa500 !important;
        color: black !important;
        z-index: 100;
        padding: 12px;
        border: 1px solid #444;
        white-space: nowrap;
    }
    
    /* ضبط خلايا المحتوى */
    .data-row td {
        border: 1px solid #444;
        text-align: center;
        padding: 0px; /* لإعطاء مساحة للمدخلات */
        height: 50px;
    }
    
    .row-even { background-color: #D6C1A6; color: black; }
    .row-odd { background-color: #1e2124; color: white; }
    
    /* تنسيق التاريخ ليظهر في سطرين صغيرين */
    .time-cell { font-size: 11px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية (Google Sheets)
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
        headers = s.row_values(1)
        col_idx = headers.index(col_name) + 1
        s.update_cell(row_idx + 2, col_idx, val)
        st.cache_resource.clear()
        st.rerun()

# 3. الواجهة البرمجية
try:
    df = get_data()
    if not df.empty:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    st.title("🛡️ الرقابة - نظام الجداول")
    
    tabs = st.tabs(["📊 الإحصائيات", "📜 السجل (History)"])

    with tabs[1]:
        st.write("⬅️ اسحب يميناً ويساراً للتنقل في الجدول")
        
        # حاوية الجدول
        st.markdown('<div class="table-viewport">', unsafe_allow_html=True)
        
        # عرض الرأس البرتقالي الثابت
        # نستخدم columns لمحاكاة الصف لكي تتماشى مع المدخلات التفاعلية
        header_cols = st.columns([0.7, 1.2, 1, 1.5, 2, 2.5])
        labels = ["تصفير", "الكمية", "الحالة", "المنتج", "المنزل", "التاريخ"]
        for col, label in zip(header_cols, labels):
            col.markdown(f'<div style="background:#ffa500; color:black; padding:10px; border:1px solid #444; text-align:center; font-weight:bold; position:sticky; top:0; z-index:10;">{label}</div>', unsafe_allow_html=True)
        
        # عرض البيانات (آخر 40 سطر)
        recent = df.tail(40).iloc[::-1]
        
        for i, row in recent.iterrows():
            bg = "#D6C1A6" if i % 2 == 0 else "#1e2124"
            tc = "black" if i % 2 == 0 else "white"
            
            # كل سطر عبارة عن مجموعة أعمدة لضمان بقائها أفقية
            r_cols = st.columns([0.7, 1.2, 1, 1.5, 2, 2.5])
            
            # 1. زر التصفير (تعديل مباشر)
            with r_cols[0]:
                if st.button("❌", key=f"z_{i}"):
                    update_val(i, 'الكمية', 0)
            
            # 2. تعديل الكمية (مربع إدخال مباشر)
            with r_cols[1]:
                new_q = st.number_input("", value=int(row['الكمية']), key=f"edit_q_{i}", label_visibility="collapsed")
                if new_q != int(row['الكمية']):
                    update_val(i, 'الكمية', new_q)
            
            # 3. الحالة
            r_cols[2].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:35px; display:flex; align-items:center; justify-content:center; font-weight:bold;">{row["الحالة"]}</div>', unsafe_allow_html=True)
            
            # 4. المنتج
            r_cols[3].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:35px; display:flex; align-items:center; justify-content:center;">{row["المنتج"]}</div>', unsafe_allow_html=True)
            
            # 5. المنزل
            r_cols[4].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:35px; display:flex; align-items:center; justify-content:center;">{row["المنزل"]}</div>', unsafe_allow_html=True)
            
            # 6. التاريخ (سطرين)
            d_parts = row['التاريخ'].split(" ")
            d_html = f"{d_parts[0]}<br>{d_parts[1]}" if len(d_parts) > 1 else row['التاريخ']
            r_cols[5].markdown(f'<div style="background:{bg}; color:{tc}; border:1px solid #444; height:35px; font-size:11px; text-align:center; display:flex; align-items:center; justify-content:center;">{d_html}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
                                     
