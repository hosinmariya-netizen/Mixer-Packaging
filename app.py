import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والخلفية (الصورة والتنسيق)
st.set_page_config(page_title="Bébé Sympa", layout="wide")

# الرابط التالي هو لصورة خلفية هادئة (يمكنك تغييره لاحقاً)
bg_img = "https://www.transparenttextures.com/patterns/dark-matter.png"

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{bg_img}");
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }}
    /* تنسيق الجداول لتسهيل السحب على الموبايل */
    div[data-testid="stDataFrame"] {{
        background: rgba(30, 33, 36, 0.85);
        border: 2px solid #ffa500;
        border-radius: 12px;
        padding: 5px;
    }}
    /* منع تكسر التبويبات */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# 2. وظائف الاتصال والبيانات
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
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            df.columns = df.columns.str.strip()
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
            return df
    return pd.DataFrame(columns=['الكمية', 'المنتج', 'المنزل', 'التاريخ', 'الحالة'])

def add_to_sheet(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)
        st.cache_resource.clear()

# 3. بناء الواجهة البرمجية
try:
    df = load_data()
    st.title("🛡️ الرقابة الذكية - Bébé Sympa")

    tabs = st.tabs(["📥 استلام", "📤 إرسال", "🏢 المخزن", "💰 كشف حساب", "📜 السجل (History)"])

    # --- 📥 الاستلام من المنازل ---
    with tabs[0]:
        st.subheader("📦 استلام بضاعة جاهزة")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
            for h in homes:
                with st.expander(f"🏠 منزل: {h}"):
                    h_df = df[df['المنزل'] == h]
                    for p in h_df['المنتج'].unique():
                        out = h_df[(h_df['المنتج'] == p) & (h_df['الحالة'].isin(['ct', 'fn']))]['الكمية'].sum()
                        rec = h_df[(h_df['المنتج'] == p) & (h_df['الحالة'] == 'st')]['الكمية'].sum()
                        diff = out - rec
                        if diff > 0:
                            st.write(f"**{p}** | متبقي: {int(diff)}")
                            val = st.number_input(f"الكمية المستلمة ({p})", min_value=0, key=f"i_{h}_{p}")
                            if st.button("تأكيد الاستلام", key=f"b_{h}_{p}"):
                                add_to_sheet([val, p, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.rerun()

    # --- 📤 الإرسال الجديد ---
    with tabs[1]:
        st.subheader("📤 إرسال بضاعة للمنازل")
        with st.form("send_form"):
            f_h = st.text_input("اسم المنزل")
            f_p = st.text_input("اسم المنتج")
            f_q = st.number_input("الكمية", min_value=1)
            f_s = st.selectbox("نوع العملية", ["ct", "fn"])
            if st.form_submit_button("إرسال الآن 🚀"):
                add_to_sheet([f_q, f_p, f_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_s])
                st.rerun()

    # --- 🏢 المخزن (مع تلوين المتوفر) ---
    with tabs[2]:
        st.subheader("🏢 رصيد المخزن المتاح")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stk = (s_in - s_out).fillna(s_in).reset_index()
            # تلوين الخانات المتوفرة (أخضر)
            st.dataframe(stk.style.highlight_between(left=1, color='#004d00'), use_container_width=True)

    # --- 💰 كشف حساب المنازل ---
    with tabs[3]:
        st.subheader("💰 ملخص الكميات عند المنازل")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    # --- 📜 السجل (التعديل + التلوين الأحمر للصفر + السحب) ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات (تعديل مباشر)")
        if not df.empty:
            hist = df.iloc[::-1].head(100).copy()
            
            # ميزة التلوين البصري: إذا كانت الكمية 0 تظهر بشكل مختلف للتنبيه
            def color_zero(val):
                color = 'red' if val == 0 else 'white'
                return f'color: {color}'

            # الجدول القابل للتعديل والسحب الأفقي
            st.data_editor(
                hist.style.applymap(color_zero, subset=['الكمية']),
                column_config={
                    "الكمية": st.column_config.NumberColumn("🔢 الكمية", width="small", format="%d"),
                    "المنتج": st.column_config.TextColumn("📦 المنتج", width="medium"),
                    "المنزل": st.column_config.TextColumn("🏠 المنزل", width="medium"),
                    "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="medium"),
                },
                use_container_width=False, # يسمح بالسحب الأفقي الحقيقي
                hide_index=True,
                key="main_editor"
            )

            st.divider()
            # زر التصفير (✓)
            st.subheader("✅ تصفير عملية")
            row_to_fix = st.selectbox("اختر سطر لتصفيره:", options=hist.index, 
                                     format_func=lambda x: f"{hist.loc[x, 'المنزل']} - {hist.loc[x, 'المنتج']} ({hist.loc[x, 'الكمية']})")
            if st.button("تصفير الكمية المختار ✓"):
                r = hist.loc[row_to_fix]
                add_to_sheet([r['الكمية'], r['المنتج'], r['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                st.success("تم التصفير!")
                st.rerun()

except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
