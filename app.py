import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* إجبار الجداول على السحب الجانبي وعدم التكسر */
    .stDataFrame { border: 1px solid #ffa500; }
    div[data-testid="stExpander"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية (الاتصال الآمن)
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

def load_data():
    sheet = get_sheet()
    if sheet:
        df = pd.DataFrame(sheet.get_all_records())
        if not df.empty:
            df.columns = df.columns.str.strip()
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def save_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)
        st.cache_resource.clear()

# 3. واجهة المستخدم الرئيسية
try:
    df = load_data()

    col_title, col_ref = st.columns([4, 1])
    col_title.title("🛡️ الرقابة - Bébé Sympa")
    if col_ref.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.rerun()

    tabs = st.tabs(["📥 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History"])

    # --- تبويب الاستلام ---
    with tabs[0]:
        st.subheader("📦 استلام من المنازل")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
            for h in homes:
                with st.expander(f"🏠 منزل: {h}"):
                    h_df = df[df['المنزل'] == h]
                    for prd in h_df['المنتج'].unique():
                        out_q = h_df[(h_df['المنتج'] == prd) & (h_df['الحالة'].isin(['ct', 'fn']))]['الكمية'].sum()
                        in_q = h_df[(h_df['المنتج'] == prd) & (h_df['الحالة'] == 'st')]['الكمية'].sum()
                        rem = out_q - in_q
                        if rem > 0:
                            st.write(f"**{prd}** (متبقي بذمة المنزل: {int(rem)})")
                            q = st.number_input(f"الكمية المستلمة", min_value=0, key=f"q_{h}_{prd}")
                            if st.button("تأكيد", key=f"b_{h}_{prd}"):
                                save_row([q, prd, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.rerun()

    # --- تبويب الإخراج ---
    with tabs[1]:
        st.subheader("📤 إرسال بضاعة جديدة")
        with st.form("out_form"):
            h_in = st.text_input("اسم المنزل")
            p_in = st.text_input("المنتج")
            q_in = st.number_input("الكمية", min_value=1)
            s_in = st.selectbox("الحالة", ["ct", "fn"])
            if st.form_submit_button("إرسال"):
                save_row([q_in, p_in, h_in, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), s_in])
                st.rerun()

    # --- تبويب المخزن ---
    with tabs[2]:
        st.subheader("🏢 رصيد المخزن الحالي")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = (s_in - s_out).fillna(s_in).reset_index()
            st.dataframe(stock[stock['الكمية'] > 0], use_container_width=True)

    # --- تبويب كشف الحساب ---
    with tabs[3]:
        st.subheader("💰 ملخص المنازل")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    # --- تبويب السجل (History) - الأفقي والقابل للتعديل ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات (اسحب لليمين واليسار)")
        if not df.empty:
            # عرض الجدول أفقياً مع إمكانية التعديل
            hist = df.iloc[::-1].head(100).copy()
            
            # محرر البيانات التفاعلي: يضمن بقاء الجدول أفقياً على الهاتف
            edited_hist = st.data_editor(
                hist,
                column_config={
                    "الكمية": st.column_config.NumberColumn("الكمية", width="small"),
                    "التاريخ": st.column_config.TextColumn("التاريخ", width="medium"),
                    "المنزل": st.column_config.TextColumn("المنزل", width="medium"),
                    "المنتج": st.column_config.TextColumn("المنتج", width="medium"),
                    "الحالة": st.column_config.TextColumn("الحالة", width="small"),
                },
                use_container_width=False, # يسمح بظهور شريط التمرير الأفقي
                hide_index=True,
                key="editor"
            )
            
            st.divider()
            # خانة التصفير السريع (✓)
            st.subheader("✅ تصفير عملية")
            to_zero = st.selectbox("اختر سطر لتصفيره", options=hist.index, 
                                   format_func=lambda x: f"{hist.loc[x, 'المنزل']} - {hist.loc[x, 'المنتج']} ({hist.loc[x, 'الكمية']})")
            if st.button("تصفير الآن ✓"):
                # الطريقة البرمجية الآمنة: إضافة عملية "استلام" بنفس الكمية لتصفير الذمة
                row = hist.loc[to_zero]
                save_row([row['الكمية'], row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                st.success("تم التصفير!")
                st.rerun()

except Exception as e:
    st.error(f"عذراً، حدث خطأ: {e}")
    
