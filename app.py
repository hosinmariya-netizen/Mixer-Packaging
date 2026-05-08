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
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    /* تحسين شكل الجداول على الهاتف */
    .stDataFrame { border: 1px solid #ffa500; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية والاتصال بـ Google Sheets
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        # استبدل الرابط برابط ملفك إذا تغير
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except Exception as e:
        st.error(f"فشل الاتصال بملف البيانات: {e}")
        return None

def load_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = df.columns.str.strip()
            # حل مشكلة الخطأ: تحويل الكمية إلى أرقام وإلغاء النصوص
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def save_new_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)
        st.cache_resource.clear()

# 3. معالجة البيانات والواجهة
try:
    df = load_data()

    # الهيدر العلوي
    col_main, col_refresh = st.columns([4, 1])
    with col_main:
        st.title("🛡️ نظام الرقابة - Bébé Sympa")
    with col_refresh:
        if st.button("🔄 تحديث"):
            st.cache_resource.clear()
            st.rerun()

    # التبويبات الخمسة الأساسية
    tabs = st.tabs(["📥 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # --- TAB 1: الاستلام من المنازل ---
    with tabs[0]:
        st.subheader("📦 استلام بضاعة من المنازل")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
            for home in homes:
                with st.expander(f"🏠 منزل: {home}"):
                    home_df = df[df['المنزل'] == home]
                    for prod in home_df['المنتج'].unique():
                        p_df = home_df[home_df['المنتget_data'] == prod]
                        # حساب المتبقي (المخرج - المستلم)
                        out_q = home_df[(home_df['المنتج'] == prod) & (home_df['الحالة'].isin(['ct', 'fn']))]['الكمية'].sum()
                        in_q = home_df[(home_df['المنتج'] == prod) & (home_df['الحالة'] == 'st')]['الكمية'].sum()
                        rem = out_q - in_q
                        if rem > 0:
                            st.write(f"**{prod}** (المتبقي: {int(rem)})")
                            q_val = st.number_input("الكمية المستلمة", min_value=0, key=f"in_{home}_{prod}")
                            if st.button("تأكيد الاستلام", key=f"btn_{home}_{prod}"):
                                save_new_row([q_val, prod, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.rerun()

    # --- TAB 2: إخراج بضاعة ---
    with tabs[1]:
        st.subheader("📤 تسجيل إخراج جديد")
        with st.form("out_form"):
            f_home = st.text_input("اسم المنزل")
            f_prod = st.text_input("المنتج")
            f_qty = st.number_input("الكمية", min_value=1)
            f_stat = st.selectbox("الحالة", ["ct", "fn"])
            if st.form_submit_button("إرسال للمنزل"):
                if f_home and f_prod:
                    save_new_row([f_qty, f_prod, f_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_stat])
                    st.success("تم الإرسال!")
                    st.rerun()

    # --- TAB 3: المخزن ---
    with tabs[2]:
        st.subheader("🏢 الرصيد المتاح بالمخزن")
        if not df.empty:
            st_sum = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            cl_sum = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = (st_sum - cl_sum).fillna(st_sum).reset_index()
            st.table(stock[stock['الكمية'] > 0])

    # --- TAB 4: كشف الحساب ---
    with tabs[3]:
        st.subheader("💰 ملخص الكميات")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    # --- TAB 5: السجل (History) - أفقي وقابل للسحب ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات الأخير")
        if not df.empty:
            # عرض الجدول بشكل أفقي احترافي يدعم السحب الجانبي
            history_display = df.iloc[::-1].head(100)
            st.dataframe(
                history_display, 
                use_container_width=True, 
                height=400,
                column_config={
                    "التاريخ": st.column_config.TextColumn("التاريخ", width="medium"),
                    "الكمية": st.column_config.NumberColumn("الكمية", format="%d")
                }
            )
            
            st.divider()
            st.subheader("🧹 تصفير سريع")
            selected_row = st.selectbox("اختر عملية لتصفيرها", options=history_display.index, 
                                        format_func=lambda x: f"{history_display.loc[x, 'المنزل']} - {history_display.loc[x, 'المنتج']} ({history_display.loc[x, 'الكمية']})")
            if st.button("تصفير الكمية المختارة ✓"):
                 # إضافة سطر معاكس للتصفير (طريقة آمنة برمجياً)
                 row = history_display.loc[selected_row]
                 save_new_row([row['الكمية'], row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st
            
