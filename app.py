import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق العام
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* تنسيق خلايا الجدول الشبيه بالإكسل */
    .excel-cell {
        border: 1px solid #444;
        padding: 8px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 50px;
        font-size: 14px;
    }
    .header-cell {
        background-color: #ffa500;
        color: black;
        font-weight: bold;
        border: 1px solid #444;
        text-align: center;
        padding: 8px;
    }
    /* ألوان الصفوف المتبادلة */
    .even-row { background-color: #D6C1A6; color: black; }
    .odd-row { background-color: #1e2124; color: white; }
    
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال بـ Google Sheets
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

# 3. معالجة البيانات والواجهة
try:
    df = get_data()
    if not df.empty:
        df.columns = df.columns.str.strip()
        if 'الكمية' in df.columns:
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    # الهيدر العلوي وزر التحديث
    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة - Bébé Sympa")
    with col_ref:
        if st.button("🔄 تحديث البيانات"):
            st.cache_resource.clear()
            st.rerun()

    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # --- TAB 1: الاستلام من المنازل ---
    with tabs[0]:
        st.subheader("📦 إدارة المستلمات من المنازل")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
            for home in homes:
                with st.expander(f"🏠 منزل: {home}"):
                    home_data = df[df['المنزل'] == home]
                    for prod in home_data['المنتج'].unique():
                        p_data = home_data[home_data['المنتج'] == prod]
                        total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                        total_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                        rem = total_out - total_in
                        if rem > 0:
                            st.write(f"**{prod}** (المتبقي بذمة المنزل: {int(rem)})")
                            c1, c2 = st.columns([3, 1])
                            qty_input = c1.number_input(f"كمية الاستلام", min_value=0, key=f"in_{home}_{prod}")
                            if c2.button("تأكيد الاستلام", key=f"btn_in_{home}_{prod}"):
                                if qty_input > 0:
                                    append_row([qty_input, prod, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                    st.cache_resource.clear()
                                    st.rerun()

    # --- TAB 2: إخراج بضاعة ---
    with tabs[1]:
        st.subheader("📤 تسجيل إخراج بضاعة للمنزل")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            o_h = f1.text_input("اسم المنزل")
            o_p = f2.text_input("اسم المنتج")
            o_q = f3.number_input("الكمية", min_value=1)
            o_s = st.radio("نوع العملية", ["ct", "fn"], horizontal=True)
            if st.form_submit_button("إرسال للمنزل"):
                if o_h and o_p:
                    append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), o_s])
                    st.cache_resource.clear()
                    st.success("تم تسجيل الإخراج")
                    st.rerun()

    # --- TAB 3: المخزن النهائي ---
    with tabs[2]:
        st.subheader("🏢 رصيد الشركة الفعلي")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = s_in.subtract(s_out, fill_value=0).reset_index()
            for _, r in stock.iterrows():
                if r['الكمية'] > 0:
                    st.info(f"📦 المنتج: {r['المنتج']} | الرصيد المتاح: {int(r['الكمية'])}")

    # --- TAB 4: كشف الحساب ---
    with tabs[3]:
        st.subheader("💰 ملخص الكميات لكل منزل")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    # --- TAB 5: السجل (History) بتصميم الإكسل ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات (Excel View)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50)
            
            # رأس الجدول الثابت (عناوين)
            h_cols = st.columns([1.5, 1.5, 1, 1, 2, 1])
            headers = ["المنزل", "المنتج", "الحالة", "الكمية", "التاريخ", "تسوية"]
            for col, txt in zip(h_cols, headers):
                col.markdown(f'<div class="header-cell">{txt}</div>', unsafe_allow_html=True)
            
            # محتوى الجدول
            for i, row in history_df.iterrows():
                bg_class = "even-row" if i % 2 == 0 else "odd-row"
                with st.container():
                    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 1, 2, 1])
                    c1.markdown(f'<div class="excel-cell {bg_class}">{row["المنزل"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="excel-cell {bg_class}">{row["المنتج"]}</div>', unsafe_allow_html=True)
                    
                    status_bg = "#ffa500" if row['الحالة'] in ['ct', 'fn'] else "transparent"
                    c3.markdown(f'<div class="excel-cell {bg_class}" style="background:{status_bg}; color:black; font-weight:bold;">{row["الحالة"]}</div>', unsafe_allow_html=True)
                    
                    c4.markdown(f'<div class="excel-cell {bg_class}">{int(row["الكمية"])}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div class="excel-cell {bg_class}">{row["التاريخ"]}</div>', unsafe_allow_html=True)
                    
                    # زر التسوية
                    if row['الحالة'] in ['ct', 'fn'] and row['المنزل'] != "-":
                        if c6.button("تصفير", key=f"set_{i}"):
                            p_data = df[(df['المنزل'] == row['المنزل']) & (df['المنتج'] == row['المنتج'])]
                            rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                            if rem > 0:
                                append_row([rem, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.rerun()
                    else:
                        c6.markdown(f'<div class="excel-cell {bg_class}">-</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"حدث خطأ تقني: {e}")
        
