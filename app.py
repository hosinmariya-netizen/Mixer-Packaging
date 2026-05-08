import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والجماليات
st.set_page_config(page_title="Bébé Sympa 2026", layout="wide")

# استعادة الخلفية وتنسيق الجداول
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/dark-matter.png");
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }
    div[data-testid="stDataFrame"] {
        background: rgba(30, 33, 36, 0.9);
        border: 2px solid #ffa500;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. إدارة البيانات (مع معالجة أخطاء dtype)
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except:
        return None

def load_clean_data():
    s = get_sheet()
    if s:
        df = pd.DataFrame(s.get_all_records())
        if not df.empty:
            df.columns = df.columns.str.strip()
            # حل مشكلة dtype: تحويل الكمية لرقم بشكل اجباري
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0).astype(int)
            return df
    return pd.DataFrame(columns=['الكمية', 'المنتج', 'المنزل', 'التاريخ', 'الحالة'])

def save_row(row):
    s = get_sheet()
    if s:
        s.append_row(row)
        st.cache_resource.clear()

# 3. بناء الواجهة
try:
    df = load_clean_data()
    st.title("🛡️ نظام الرقابة الذكي")

    tabs = st.tabs(["📥 استلام", "📤 إرسال", "🏢 المخزن", "💰 كشف حساب", "📜 السجل (تعديل)"])

    # --- 1. الاستلام ---
    with tabs[0]:
        st.subheader("🏠 استلام من المنازل")
        homes = [h for h in df['المنزل'].unique() if str(h).strip() not in ["", "-"]]
        for h in homes:
            with st.expander(f"🏠 منزل: {h}"):
                h_df = df[df['المنزل'] == h]
                for p in h_df['المنتج'].unique():
                    # حساب الفرق بدقة (رقم مع رقم)
                    sent = h_df[h_df['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                    received = h_df[h_df['الحالة'] == 'st']['الكمية'].sum()
                    rem = sent - received
                    if rem > 0:
                        st.write(f"📦 **{p}** | الباقي: {rem}")
                        in_qty = st.number_input(f"الكمية المستلمة ({p})", min_value=0, key=f"q_{h}_{p}")
                        if st.button("حفظ الاستلام ✅", key=f"btn_{h}_{p}"):
                            save_row([int(in_qty), p, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                            st.rerun()

    # --- 2. الإرسال ---
    with tabs[1]:
        st.subheader("📤 إرسال بضاعة")
        with st.form("send_f"):
            f_h = st.text_input("اسم المنزل")
            f_p = st.text_input("المنتج")
            f_q = st.number_input("الكمية", min_value=1)
            f_s = st.selectbox("الحالة", ["ct", "fn"])
            if st.form_submit_button("إرسال الآن"):
                save_row([int(f_q), f_p, f_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_s])
                st.rerun()

    # --- 3. المخزن ---
    with tabs[2]:
        st.subheader("🏢 الرصيد الحالي")
        st_sum = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        cl_sum = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        stock = (st_sum - cl_sum).fillna(st_sum).reset_index()
        st.dataframe(stock.style.highlight_between(left=1, color='#004d00'), use_container_width=True)

    # --- 4. كشف الحساب ---
    with tabs[3]:
        st.subheader("💰 ذمم المنازل")
        pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
        st.dataframe(pivot, use_container_width=True)

    # --- 5. السجل (التعديل، التلوين، التصفير، والسحب السلس) ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات")
        hist = df.iloc[::-1].head(50).copy()
        
        # التلوين: الأحمر للصفر (رقابة بصرية)
        def color_rule(val):
            return 'background-color: #8b0000' if val == 0 else ''

        # الجدول المرن (سحب لليسار)
        edited = st.data_editor(
            hist.style.applymap(color_rule, subset=['الكمية']),
            column_config={
                "الكمية": st.column_config.NumberColumn("🔢 الكمية", width="small"),
                "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="medium"),
                "المنتج": st.column_config.TextColumn("📦 المنتج", width="small"),
                "المنزل": st.column_config.TextColumn("🏠 المنزل", width="small"),
            },
            hide_index=True,
            use_container_width=False # تفعيل السحب الأفقي
        )

        st.divider()
        # زر التصفير (جديد)
        st.subheader("❌ تصفير عملية")
        to_del = st.selectbox("اختر العملية المراد تصفيرها:", options=hist.index, 
                              format_func=lambda x: f"{hist.loc[x, 'المنزل']} - {hist.loc[x, 'المنتج']} ({hist.loc[x, 'الكمية']})")
        if st.button("تصفير هذه العملية الآن ✓"):
            target = hist.loc[to_del]
            save_row([int(target['الكمية']), target['المنتج'], target['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
            st.success("تم التصفير بنجاح!")
            st.rerun()

except Exception as e:
    st.error(f"حدث خطأ في النظام: {str(e)}")
                    
