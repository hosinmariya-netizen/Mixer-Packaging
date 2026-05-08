import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الواجهة
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* ستايل الجدول الأفقي */
    .excel-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .excel-table th { background-color: #ffa500; color: black; border: 1px solid #444; padding: 10px; position: sticky; top: 0; }
    .excel-table td { border: 1px solid #444; padding: 8px; text-align: center; }
    .row-even { background-color: #D6C1A6; color: black; }
    .row-odd { background-color: #1e2124; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية
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

def append_row(row):
    s = get_sheet()
    if s: s.append_row(row)

# 3. بناء الواجهة (تأكد من بقاء المسافات كما هي هنا)
try:
    df = get_data()
    if not df.empty:
        df.columns = df.columns.str.strip()
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    # الهيدر وزر التحديث
    c_t, c_r = st.columns([4, 1])
    c_t.title("🛡️ نظام الرقابة - Bébé Sympa")
    if c_r.button("🔄 تحديث البيانات"):
        st.cache_resource.clear()
        st.rerun()

    t = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    with t[0]:
        st.subheader("📦 استلام من المنازل")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
            for home in homes:
                with st.expander(f"🏠 منزل: {home}"):
                    h_df = df[df['المنزل'] == home]
                    for prd in h_df['المنتج'].unique():
                        p_df = h_df[h_df['المنتج'] == prd]
                        rem = p_df[p_df['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_df[p_df['الحالة'] == 'st']['الكمية'].sum()
                        if rem > 0:
                            st.write(f"**{prd}** | متبقي: {int(rem)}")
                            col1, col2 = st.columns([3, 1])
                            q = col1.number_input(f"الكمية", min_value=0, key=f"q_{home}_{prd}")
                            if col2.button("تأكيد", key=f"b_{home}_{prd}"):
                                append_row([q, prd, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.rerun()

    with t[1]:
        st.subheader("📤 إخراج بضاعة")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            o_h = f1.text_input("اسم المنزل")
            o_p = f2.text_input("المنتج")
            o_q = f3.number_input("الكمية", min_value=1)
            o_s = st.radio("الحالة", ["ct", "fn"], horizontal=True)
            if st.form_submit_button("إرسال"):
                append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), o_s])
                st.cache_resource.clear()
                st.rerun()

    with t[2]:
        st.subheader("🏢 المخزن")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stk = s_in.subtract(s_out, fill_value=0)
            for p, q in stk.items():
                if q > 0: st.info(f"📦 {p}: {int(q)}")

    with t[3]:
        st.subheader("💰 كشف الحساب")
        if not df.empty:
            st.dataframe(df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0))

    with t[4]:
        st.subheader("📜 History (Excel Style)")
        if not df.empty:
            hist = df.iloc[::-1].head(50)
            # إنشاء الجدول الأفقي بـ HTML
            html = '<div style="overflow-x:auto;"><table class="excel-table"><thead><tr>'
            for col in ["المنزل", "المنتج", "الحالة", "الكمية", "التاريخ"]:
                html += f'<th>{col}</th>'
            html += '</tr></thead><tbody>'
            
            for i, row in hist.iterrows():
                cls = "row-even" if i % 2 == 0 else "row-odd"
                html += f'<tr class="{cls}">'
                html += f'<td>{row["المنزل"]}</td><td>{row["المنتج"]}</td><td>{row["الحالة"]}</td>'
                html += f'<td>{int(row["الكمية"])}</td><td>{row["التاريخ"]}</td></tr>'
            
            html += '</tbody></table></div>'
            st.markdown(html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"خطأ: {e}")
                                            
