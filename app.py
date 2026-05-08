import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق الجمالي
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
    .history-row-even { background-color: #D6C1A6; color: #000; padding: 5px; border-radius: 5px; margin-bottom: 2px; }
    .history-row-odd { background-color: rgba(255, 165, 0, 0.1); color: #fff; padding: 5px; border-radius: 5px; margin-bottom: 2px; border: 1px solid #ffa500; }
    .stButton>button { border-radius: 8px; }
    .warning-text { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال ببيانات جوجل
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
        df = pd.DataFrame(data)
        expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_cols]
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# 3. معالجة البيانات والواجهة
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    # الهيدر العلوي
    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة المطور")
    with col_ref:
        if st.button("🔄 تحديث"):
            st.cache_resource.clear()
            st.session_state.df = get_data()
            st.rerun()

    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # --- TAB 1: استلام من المنزل ---
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
                                if qty_in > 0:
                                    append_row([qty_in, prod, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                    st.cache_resource.clear()
                                    st.session_state.df = get_data()
                                    st.success("✅ تمت العملية بنجاح")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ يرجى إدخال كمية صحيحة")

    # --- TAB 2: إخراج للمنزل ---
    with tabs[1]:
        st.subheader("📤 إخراج بضاعة جديدة")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            o_h = f1.text_input("اسم المنزل")
            o_p = f2.text_input("اسم المنتج")
            o_q = f3.number_input("الكمية", min_value=1)
            o_s = st.radio("الحالة", ["ct", "fn"], horizontal=True)
            if st.form_submit_button("تسجيل الخروج"):
                if o_q > 0 and o_p.strip() and o_h.strip():
                    append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), o_s])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success("✅ تم تسجيل العملية بنجاح")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 3: المخزن النهائي ---
    with tabs[2]:
        st.subheader("🏢 رصيد الشركة")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = s_in.subtract(s_out, fill_value=0).reset_index()
            total_stock = stock['الكمية'].sum()
            st.metric("إجمالي الرصيد", f"{int(total_stock)} قطعة")
            for _, r in stock.iterrows():
                if r['الكمية'] > 0:
                    st.info(f"📦 {r['المنتج']}: {int(r['الكمية'])} قطعة متوفرة")

    # --- TAB 4: كشف الحساب ---
    with tabs[3]:
        if not df.empty:
            st.dataframe(df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0), use_container_width=True)

    # --- TAB 5: السجل (HISTORY) ---
    with tabs[4]:
        st.subheader("📜 سجل المعاملات (History)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50)
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("السجل فارغ حالياً.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
