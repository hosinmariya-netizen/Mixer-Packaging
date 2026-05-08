import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="Bébé Sympa Pro", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/dark-matter.png");
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }
    div[data-testid="stDataFrame"] {
        background: rgba(30, 33, 36, 0.9) !important;
        border: 2px solid #ffa500 !important;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف البيانات مع تنظيف صارم (حل مشكلة TypeError)
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

def load_data_safely():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            df.columns = df.columns.str.strip()
            # حل جذري للخطأ: تحويل أي شيء ليس رقماً إلى صفر ثم إلى رقم صحيح
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0).astype(int)
            return df
    return pd.DataFrame(columns=['الكمية', 'المنتج', 'المنزل', 'التاريخ', 'الحالة'])

def save_entry(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)
        st.cache_resource.clear()

# 3. بناء واجهة المستخدم
try:
    df = load_data_safely()
    st.title("🛡️ نظام الرقابة الاحترافي")

    # تحديث يدوي للبيانات
    if st.button("🔄 تحديث السيرفر"):
        st.cache_resource.clear()
        st.rerun()

    tabs = st.tabs(["📥 استلام", "📤 إرسال", "🏢 المخزن", "💰 الحسابات", "📜 السجل"])

    with tabs[0]:
        st.subheader("🏠 استلام من المنازل")
        homes = [h for h in df['المنزل'].unique() if str(h).strip() not in ["", "-"]]
        for h in homes:
            with st.expander(f"🏠 منزل: {h}"):
                h_df = df[df['المنزل'] == h]
                for p in h_df['المنتج'].unique():
                    # حسابات رياضية آمنة تماماً الآن
                    sent = h_df[h_df['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                    received = h_df[h_df['الحالة'] == 'st']['الكمية'].sum()
                    rem = int(sent) - int(received)
                    if rem > 0:
                        st.write(f"📦 **{p}** | متبقي: {rem}")
                        val = st.number_input(f"الكمية ({p})", min_value=0, key=f"in_{h}_{p}")
                        if st.button("تأكيد ✅", key=f"btn_{h}_{p}"):
                            save_entry([int(val), p, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                            st.rerun()

    with tabs[1]:
        st.subheader("📤 إرسال جديد")
        with st.form("send_form"):
            f_h = st.text_input("اسم المنزل")
            f_p = st.text_input("اسم المنتج")
            f_q = st.number_input("الكمية", min_value=1)
            f_s = st.selectbox("الحالة", ["ct", "fn"])
            if st.form_submit_button("إرسال الآن"):
                save_entry([int(f_q), f_p, f_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_s])
                st.rerun()

    with tabs[2]:
        st.subheader("🏢 رصيد المخزن")
        if not df.empty:
            st_sum = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            cl_sum = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = (st_sum - cl_sum).fillna(st_sum).reset_index()
            st.dataframe(stock.style.highlight_between(left=1, color='#004d00'), use_container_width=True)

    with tabs[3]:
        st.subheader("💰 ملخص ذمم المنازل")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    with tabs[4]:
        st.subheader("📜 السجل (History)")
        if not df.empty:
            hist = df.iloc[::-1].head(50).copy()
            
            # جدول سلس، بدون فراغات، وقابل للسحب يميناً ويساراً
            st.data_editor(
                hist,
                column_config={
                    "الكمية": st.column_config.NumberColumn("🔢 الكمية", width="small"),
                    "المنتج": st.column_config.TextColumn("📦 المنتج", width="small"),
                    "المنزل": st.column_config.TextColumn("🏠 المنزل", width="small"),
                    "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="medium"),
                },
                use_container_width=False, # هذا يضمن سلاسة السحب على الموبايل
                hide_index=True
            )

            st.divider()
            st.subheader("❌ زر التصفير السريع")
            to_fix = st.selectbox("اختر العملية لتصفيرها:", options=hist.index, 
                                 format_func=lambda x: f"{hist.loc[x, 'المنزل']} - {hist.loc[x, 'المنتج']} ({hist.loc[x, 'الكمية']})")
            if st.button("تصفير الآن ✓"):
                r = hist.loc[to_fix]
                save_entry([int(r['الكمية']), r['المنتج'], r['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                st.success("تم التصفير!")
                st.rerun()

except Exception as e:
    st.error(f"⚠️ خطأ تقني: {str(e)}")
    st.info("نصيحة: تأكد أن عمود الكمية في الإكسل لا يحتوي على كلمات، فقط أرقام.")
    
