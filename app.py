import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Bébé Sympa", layout="wide")

# 2. تصميم CSS لإجبار الجدول على التمدد أفقياً وتثبيت الرأس
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    
    /* الحاوية السحرية التي تمنع التكسير وتسمح بالسحب الجانبي */
    .mega-scroll {
        width: 100%;
        overflow-x: auto; /* يسمح بالسحب يميناً ويساراً */
        overflow-y: auto;
        max-height: 600px;
        border: 2px solid #444;
    }

    table {
        width: auto; /* لا تجبره على عرض الشاشة */
        min-width: 1000px; /* إجبار الجدول أن يكون عريضاً جداً */
        border-collapse: collapse;
        white-space: nowrap; /* منع النص من النزول لسطر جديد */
    }

    th {
        position: sticky;
        top: 0;
        background-color: #ffa500 !important;
        color: black !important;
        z-index: 999;
        padding: 15px;
        border: 1px solid #444;
        text-align: center;
    }

    td {
        padding: 10px;
        border: 1px solid #444;
        text-align: center;
        vertical-align: middle;
    }

    .row-even { background-color: #D6C1A6; color: black; }
    .row-odd { background-color: #1e2124; color: white; }
    
    /* تنسيق خاص للأزرار داخل الجدول */
    .btn-zero { background-color: #ff4b4b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)

# 3. الدوال البرمجية (Google Sheets)
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
    return pd.DataFrame(s.get_all_records()) if s else pd.DataFrame()

def update_val(row_idx, new_q):
    s = get_sheet()
    if s:
        # نفترض أن "الكمية" هي العمود رقم 1 في الإكسل
        s.update_cell(row_idx + 2, 1, new_q)
        st.cache_resource.clear()
        st.rerun()

# 4. بناء الواجهة
try:
    df = get_data()
    st.title("🛡️ الرقابة - جدول أفقي")
    
    tabs = st.tabs(["🏠 الإدارة", "📜 History"])

    with tabs[1]:
        if not df.empty:
            st.write("⬅️ اسحب الجدول لليسار برؤية باقي البيانات")
            
            # بناء الجدول يدوياً بـ HTML لضمان عدم التلاعب به من قبل ستريمليت
            recent = df.tail(50).iloc[::-1]
            
            html_table = '<div class="mega-scroll"><table>'
            html_table += '<thead><tr><th>تصفير</th><th>الكمية</th><th>الحالة</th><th>المنتج</th><th>المنزل</th><th>التاريخ</th></tr></thead>'
            html_table += '<tbody>'
            
            for i, row in recent.iterrows():
                cls = "row-even" if i % 2 == 0 else "row-odd"
                # تقسيم التاريخ لسطرين
                dt = row['التاريخ'].replace(" ", "<br>")
                
                # ملاحظة: الأزرار والمدخلات سنضعها عبر st.columns داخل الـ HTML لتعمل برمجياً
                html_table += f'<tr class="{cls}">'
                html_table += f'<td id="btn_{i}"></td>' # مكان الزر
                html_table += f'<td id="qty_{i}"></td>' # مكان تعديل الكمية
                html_table += f'<td>{row["الحالة"]}</td>'
                html_table += f'<td>{row["المنتج"]}</td>'
                html_table += f'<td>{row["المنزل"]}</td>'
                html_table += f'<td>{dt}</td>'
                html_table += '</tr>'
            
            html_table += '</tbody></table></div>'
            st.markdown(html_table, unsafe_allow_html=True)

            # الآن نضع "الأدوات التفاعلية" فوق الجدول أو في أعمدة لتعمل
            st.divider()
            st.subheader("🛠️ أدوات التعديل السريع")
            edit_col1, edit_col2 = st.columns(2)
            
            with edit_col1:
                idx_to_zero = st.selectbox("اختر السطر للتصفير (بالمنزل والمنتج)", 
                                           options=recent.index, 
                                           format_func=lambda x: f"{recent.loc[x, 'المنزل']} - {recent.loc[x, 'المنتج']}")
                if st.button("تصفير الكمية الآن ❌"):
                    update_val(idx_to_zero, 0)
            
            with edit_col2:
                new_q_val = st.number_input("تعديل كمية السطر المختار", min_value=0)
                if st.button("حفظ الكمية الجديدة ✅"):
                    update_val(idx_to_zero, new_q_val)
        else:
            st.info("السجل فارغ")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
