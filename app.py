import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .stButton>button { border-radius: 10px; }
    .warning-text { color: #ff4b4b; font-weight: bold; padding: 10px; border: 1px solid #ff4b4b; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
    return sheet.sheet1

def get_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def append_row(row):
    sheet = get_sheet()
    sheet.append_row(row)

try:
    df = get_data()
    df.columns = df.columns.str.strip()
    if 'الكمية' in df.columns:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة والاستلام")
    with col_ref:
        if st.button("🔄 تحديث البيانات"):
            st.cache_resource.clear()
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏠 استلام من المنازل", "🏢 المخزن النهائي", "💰 كشف الحساب"])

    with tab1:
        st.subheader("📦 إدارة المستلمات من المنازل")
        homes = [h for h in df['المنزل'].unique() if h != "-"]

        for home in homes:
            home_data = df[df['المنزل'] == home]
            prods = home_data['المنتج'].unique()

            pending_count = 0
            for prod in prods:
                p_data = home_data[home_data['المنتج'] == prod]
                total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                already_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                if total_out - already_in > 0:
                    pending_count += 1

            badge = f"🟢 {pending_count}" if pending_count > 0 else "🔴 0"
            label = f"🏠 منزل: {home}  {badge}"

            with st.expander(label):
                for prod in prods:
                    p_data = home_data[home_data['المنتج'] == prod]
                    total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                    already_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    max_allowed = total_out - already_in

                    if max_allowed > 0:
                        st.markdown(f"--- \n **المنتج:** {prod}")
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            input_qty = st.number_input(f"الكمية المستلمة (الحد الأقصى {int(max_allowed)})",
                                                       min_value=0, step=1, key=f"qty_{home}_{prod}")
                        is_over = input_qty > max_allowed
                        ignore_warning = False
                        if is_over:
                            st.markdown(f'<p class="warning-text">⚠️ تحذير: الكمية ({int(input_qty)}) أكبر من الصادرة ({int(max_allowed)})!</p>', unsafe_allow_html=True)
                            ignore_warning = st.checkbox("تجاهل التحذير", key=f"ign_{home}_{prod}")
                        with c2:
                            btn_disabled = is_over and not ignore_warning
                            if st.button(f"✓ تأكيد الاستلام", key=f"btn_{home}_{prod}", disabled=btn_disabled):
                                if input_qty > 0:
                                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    append_row([input_qty, prod, home, now, "st"])
                                    st.cache_resource.clear()
                                    st.success("تم تسجيل الاستلام بنجاح!")
                                    st.rerun()
                    else:
                        st.caption(f"✅ {prod}: تم استلام كامل الكمية الصادرة.")

    with tab2:
        st.subheader("🏢 رصيد الشركة الحالي")
        stock_final = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum().reset_index()
        stock_final.columns = ['اسم المنتج', 'المخزن (st)']
        st.table(stock_final)

    with tab3:
        st.subheader("💰 ملخص العمليات المنجزة للدفع")
        payment_summary = df[df['الحالة'].isin(['ct', 'fn'])].groupby(['المنزل', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
        st.dataframe(payment_summary, use_container_width=True)

except Exception as e:
    st.error(f"خطأ في البيانات: {e}")
