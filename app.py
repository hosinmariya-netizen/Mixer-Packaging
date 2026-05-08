import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
        direction: rtl;
        background-image: url("https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(14, 17, 23, 0.92);
        z-index: 0;
    }
    .history-cell { border: 1px solid #444; padding: 5px; text-align: center; font-size: 13px; }
    .stButton>button { border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال
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

    # الرأس
    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة - Bébé Sympa")
    with col_ref:
        if st.button("🔄 تحديث"):
            st.cache_resource.clear()
            st.rerun()

    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # --- TAB 1: الاستلام ---
    with tabs[0]:
        st.subheader("📦 استلام الإنتاج")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
            for home in homes:
                with st.expander(f"🏠 منزل: {home}"):
                    home_data = df[df['المنزل'] == home]
                    for prod in home_data['المنتج'].unique():
                        p_data = home_data[home_data['المنتج'] == prod]
                        rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                        if rem > 0:
                            st.write(f"**{prod}** (المتبقي: {int(rem)})")
                            c1, c2 = st.columns([3, 1])
                            qty_in = c1.number_input(f"الكمية", min_value=0, key=f"in_{home}_{prod}")
                            if c2.button("تأكيد", key=f"btn_in_{home}_{prod}"):
                                append_row([qty_in, prod, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.rerun()

    # --- TAB 2: الإخراج ---
    with tabs[1]:
        st.subheader("📤 إخراج بضاعة للمنزل")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            o_h = f1.text_input("اسم المنزل")
            o_p = f2.text_input("اسم المنتج")
            o_q = f3.number_input("الكمية", min_value=1)
            o_s = st.radio("الحالة", ["ct", "fn"], horizontal=True)
            if st.form_submit_button("تسجيل الخروج"):
                append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), o_s])
                st.cache_resource.clear()
                st.rerun()

    # --- TAB 3: المخزن ---
    with tabs[2]:
        st.subheader("🏢 رصيد الشركة")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = s_in.subtract(s_out, fill_value=0).reset_index()
            for _, r in stock.iterrows():
                if r['الكمية'] > 0:
                    st.info(f"📦 {r['المنتج']}: {int(r['الكمية'])} قطعة")

    # --- TAB 4: كشف الحساب ---
    with tabs[3]:
        if not df.empty:
            st.dataframe(df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0), use_container_width=True)

    # --- TAB 5: السجل (History) - إصلاح المسافات وتصميم الإكسل ---
    with tabs[4]:
        st.subheader("📜 سجل المعاملات (Excel Style)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50)
            
            # رأس الجدول
            h_cols = st.columns([1.5, 1.5, 1, 1, 2, 1])
            headers = ["المنزل", "المنتج", "الحالة", "الكمية", "التاريخ", "الإجراء"]
            for col, txt in zip(h_cols, headers):
                col.markdown(f'<div style="background:#ffa500; color:black; border:1px solid #444; padding:5px; text-align:center; font-weight:bold;">{txt}</div>', unsafe_allow_html=True)
            
            for i, row in history_df.iterrows():
                bg = "#D6C1A6" if i % 2 == 0 else "transparent"
                tx = "black" if i % 2 == 0 else "white"
                
                with st.container():
                    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 1, 2, 1])
                    c1.markdown(f'<div class="history-cell" style="background:{bg}; color:{tx};">{row["المنزل"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="history-cell" style="background:{bg}; color:{tx};">{row["المنتج"]}</div>', unsafe_allow_html=True)
                    
                    st_bg = "#ffa500" if row['الحالة'] in ['ct', 'fn'] else bg
                    c3.markdown(f'<div class="history-cell" style="background:{st_bg}; color:black; font-weight:bold;">{row["الحالة"]}</div>', unsafe_allow_html=True)
                    
                    c4.markdown(f'<div class="history-cell" style="background:{bg}; color:{tx};">{int(row["الكمية"])}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div class="history-cell" style="background:{bg}; color:{tx};">{row["التاريخ"]}</div>', unsafe_allow_html=True)
                    
                    if row['الحالة'] in ['ct', 'fn'] and row['المنزل'] != "-":
                        if c6.button("تسوية", key=f"settle_{i}"):
                            p_data = df[(df['المنزل'] == row['المنزل']) & (df['المنتج'] == row['المنتج'])]
                            actual_rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                            if actual_rem > 0:
                                append_row([actual_rem, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.rerun()
                    else:
                        c6.markdown(f'<div class="history-cell" style="background:{bg}; color:{tx};">-</div>', unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات سجل.")

except Exception as e:
    st.error(f"خطأ في البيانات: {e}")
                                
