import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق العام
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# ستايل CSS مخصص لتثبيت الرأس وتصميم الإكسل
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        direction: rtl;
    }
    /* حاوية الجدول مع خاصية التمرير */
    .table-container {
        max-height: 600px;
        overflow-y: auto;
        border: 2px solid #444;
        border-radius: 5px;
    }
    /* تصميم رأس الجدول الثابت */
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 10;
        background-color: #ffa500;
        color: black;
        display: flex;
        font-weight: bold;
        border-bottom: 2px solid #444;
    }
    /* تصميم الصفوف */
    .row-style { display: flex; border-bottom: 1px solid #444; }
    .cell {
        flex: 1;
        padding: 8px;
        border-left: 1px solid #444;
        text-align: center;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .cell:last-child { border-left: none; }
    
    /* ألوان الصفوف المتبادلة */
    .even-row { background-color: #D6C1A6; color: black; }
    .odd-row { background-color: #1e2124; color: white; }
    
    .stButton>button { border-radius: 4px; height: 30px; line-height: 1; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال (تبقى كما هي لضمان عمل قاعدة البيانات)
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

def get_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# 3. البرنامج الرئيسي
try:
    df = get_data()
    if not df.empty:
        df.columns = df.columns.str.strip()
        if 'الكمية' in df.columns:
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    st.title("🛡️ نظام الرقابة الذكي")
    
    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # (ملاحظة: التبويبات 1-4 تبقى بنفس المنطق السابق، سأركز هنا على تبويب History المطلوب)

    with tabs[4]:
        st.subheader("📜 سجل المعاملات (Excel Style + Fixed Header)")
        if not df.empty:
            history_df = df.iloc[::-1] # عرض كل البيانات، الأحدث أولاً
            
            # بداية حاوية الجدول الثابت
            html_content = """
            <div class="table-container">
                <div class="sticky-header">
                    <div class="cell" style="flex:1.5">المنزل</div>
                    <div class="cell" style="flex:1.5">المنتج</div>
                    <div class="cell" style="flex:1">الحالة</div>
                    <div class="cell" style="flex:1">الكمية</div>
                    <div class="cell" style="flex:2">التاريخ</div>
                    <div class="cell" style="flex:1">إجراء</div>
                </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)

            # عرض الصفوف
            for i, row in history_df.iterrows():
                row_class = "even-row" if i % 2 == 0 else "odd-row"
                status_color = "#ffa500" if row['الحالة'] in ['ct', 'fn'] else "transparent"
                
                # إنشاء الصف باستخدام columns لمحاكاة مظهر الجدول مع أزرار Streamlit
                with st.container():
                    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 1, 2, 1])
                    
                    # نستخدم markdown لكل خلية لضبط الشكل
                    c1.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px;">{row["المنزل"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px;">{row["المنتج"]}</div>', unsafe_allow_html=True)
                    c3.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px; background:{status_color}; color:black; font-weight:bold;">{row["الحالة"]}</div>', unsafe_allow_html=True)
                    c4.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px;">{int(row["الكمية"])}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px;">{row["التاريخ"]}</div>', unsafe_allow_html=True)
                    
                    # زر التسوية
                    if row['الحالة'] in ['ct', 'fn'] and row['المنزل'] != "-":
                        if c6.button("تسوية", key=f"settle_btn_{i}"):
                            p_data = df[(df['المنزل'] == row['المنزل']) & (df['المنتج'] == row['المنتج'])]
                            actual_rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                            if actual_rem > 0:
                                append_row([actual_rem, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.rerun()
                    else:
                        c6.markdown(f'<div class="cell {row_class}" style="width:100%; height:45px;">-</div>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True) # إغلاق حاوية التمرير
        else:
            st.info("لا توجد بيانات سجل.")

    # أضف هنا بقية منطق التبويبات الأخرى (استلام، إخراج، مخزن) كما في الكود السابق

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
