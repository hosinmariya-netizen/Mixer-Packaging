import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والتصميم (CSS) لضبط الهاتف وتثبيت الرأس
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* حاوية الجدول للسماح بالتحرك الجانبي وتثبيت الرأس */
    .table-wrapper {
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #444;
    }
    
    table { width: 100%; border-collapse: collapse; min-width: 600px; }
    
    /* تثبيت الرأس البرتقالي في أعلى الشاشة */
    th {
        position: sticky;
        top: 0;
        background-color: #ffa500 !important;
        color: black !important;
        z-index: 10;
        padding: 10px;
        border: 1px solid #444;
    }
    
    td { border: 1px solid #444; padding: 8px; text-align: center; vertical-align: middle; }
    .row-even { background-color: #D6C1A6; color: black; }
    .row-odd { background-color: #1e2124; color: white; }
    
    /* تصغير الخط للتاريخ ليناسب سطرين */
    .date-text { font-size: 11px; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال ببيانات جوجل
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

def update_cell(row_idx, col_name, value):
    s = get_sheet()
    if s:
        # +2 لأن بايثون يبدأ من 0 والجدول فيه هيدر ويبدأ من 1
        col_idx = s.find(col_name).col
        s.update_cell(row_idx + 2, col_idx, value)

def append_row(row_data):
    s = get_sheet()
    if s: s.append_row(row_data)

# 3. بناء الواجهة
try:
    df = get_data()
    if not df.empty:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    # الهيدر وزر التحديث
    c1, c2 = st.columns([4, 1])
    c1.title("🛡️ الرقابة الذكية")
    if c2.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.rerun()

    tabs = st.tabs(["🏠 استلام/إخراج", "🏢 المخزن", "💰 الحساب", "📜 History"])

    # --- تبويب الإدخال (دمج الاستلام والإخراج لسهولة الهاتف) ---
    with tabs[0]:
        with st.expander("➕ إضافة عملية جديدة (إخراج للمنزل)"):
            with st.form("new_op"):
                f1, f2 = st.columns(2)
                home_in = f1.text_input("المنزل")
                prod_in = f1.text_input("المنتج")
                qty_in = f2.number_input("الكمية", min_value=1)
                stat_in = f2.selectbox("الحالة", ["ct", "fn", "st", "cl"])
                if st.form_submit_button("حفظ العملية"):
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    append_row([qty_in, prod_in, home_in, now, stat_in])
                    st.cache_resource.clear()
                    st.success("تم الحفظ!")
                    st.rerun()

    # --- تبويب السجل التاريخي (History) - هو المطلب الأساسي ---
    with tabs[3]:
        st.subheader("السجل (تثبيت الرأس + تعديل مباشر)")
        if not df.empty:
            # سنعرض آخر 40 عملية للتعديل عليها
            recent_df = df.tail(40).iloc[::-1] 
            
            # عرض رأس الجدول الثابت يدوياً باستخدام HTML لضمان الشكل
            st.markdown("""
                <div class='table-wrapper'>
                    <table>
                        <thead>
                            <tr>
                                <th>تصفير</th>
                                <th>الكمية</th>
                                <th>الحالة</th>
                                <th>المنتج</th>
                                <th>المنزل</th>
                                <th>التاريخ</th>
                            </tr>
                        </thead>
                        <tbody>
            """, unsafe_allow_html=True)

            for i, row in recent_df.iterrows():
                row_idx = i # الحفظ الأصلي في ملف جوجل
                bg_cls = "row-even" if i % 2 == 0 else "row-odd"
                date_split = row['التاريخ'].split(" ")
                date_html = f"<div class='date-text'>{date_split[0]}<br>{date_split[1] if len(date_split)>1 else ''}</div>"
                
                # استخدام أعمدة ستريمليت داخل السجل للسماح بالتفاعل (الأزرار والمدخلات)
                col_check, col_qty, col_stat, col_prod, col_home, col_date = st.columns([1, 1.5, 1, 1.5, 1.5, 2])
                
                with col_check:
                    if st.button("❌", key=f"zero_{i}"):
                        update_cell(row_idx, 'الكمية', 0)
                        st.cache_resource.clear()
                        st.rerun()
                
                with col_qty:
                    new_q = st.number_input("", value=int(row['الكمية']), key=f"edit_q_{i}", label_visibility="collapsed")
                    if new_q != int(row['الكمية']):
                        update_cell(row_idx, 'الكمية', new_q)
                        st.cache_resource.clear()
                        st.rerun()
                
                with col_stat: st.markdown(f"<div class='excel-cell {bg_cls}'>{row['الحالة']}</div>", unsafe_allow_html=True)
                with col_prod: st.markdown(f"<div class='excel-cell {bg_cls}'>{row['المنتج']}</div>", unsafe_allow_html=True)
                with col_home: st.markdown(f"<div class='excel-cell {bg_cls}'>{row['المنزل']}</div>", unsafe_allow_html=True)
                with col_date: st.markdown(f"<div class='excel-cell {bg_cls}'>{date_html}</div>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin:2px; border:0.5px solid #444'>", unsafe_allow_html=True)

    # بقية التبويبات (المخزن والحساب)
    with tabs[1]:
        st.subheader("🏢 رصيد الشركة")
        s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        stock = s_in.subtract(s_out, fill_value=0)
        st.write(stock)

except Exception as e:
    st.error(f"خطأ: {e}")
    
