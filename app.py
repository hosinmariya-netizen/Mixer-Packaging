import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة والتنسيق
st.set_page_config(page_title="Bébé Sympa", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    [data-testid="stDataFrame"] { border: 1px solid #ffa500; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e2124; 
        border-radius: 5px; 
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية (الاتصال والبيانات)
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").sheet1
    except: return None

def load_data():
    s = get_sheet()
    if s:
        df = pd.DataFrame(s.get_all_records())
        if not df.empty:
            df.columns = df.columns.str.strip()
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def save_new_row(row_list):
    s = get_sheet()
    if s:
        s.append_row(row_list)
        st.cache_resource.clear()

# 3. بناء الواجهة البرمجية (الأقسام الخمسة)
try:
    df = load_data()
    
    st.title("🛡️ نظام الرقابة المتكامل")
    
    tabs = st.tabs(["📥 استلام من منزل", "📤 إرسال جديد", "🏢 المخزن", "💰 كشف حساب", "📜 السجل (History)"])

    # --- 1. نافذة الاستلام (المنازل) ---
    with tabs[0]:
        st.subheader("📦 استلام بضاعة جاهزة")
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
                            st.write(f"**{prd}** (المتبقي عند المنزل: {int(rem)})")
                            q_val = st.number_input(f"الكمية المستلمة من {prd}", min_value=0, key=f"in_{h}_{prd}")
                            if st.button("تأكيد الاستلام ✅", key=f"btn_{h}_{prd}"):
                                save_new_row([q_val, prd, h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.rerun()

    # --- 2. نافذة الإرسال (الإخراج) ---
    with tabs[1]:
        st.subheader("📤 إرسال بضاعة إلى منزل")
        with st.form("send_form"):
            f_home = st.text_input("اسم المنزل")
            f_prod = st.text_input("اسم المنتج")
            f_qty = st.number_input("الكمية المرسلة", min_value=1)
            f_stat = st.selectbox("نوع العملية", ["ct", "fn"])
            if st.form_submit_button("إرسال الآن 🚀"):
                save_new_row([f_qty, f_prod, f_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), f_stat])
                st.rerun()

    # --- 3. نافذة المخزن ---
    with tabs[2]:
        st.subheader("🏢 رصيد المخزن الحالي")
        if not df.empty:
            st_sum = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            cl_sum = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
            stock = (st_sum - cl_sum).fillna(st_sum).reset_index()
            st.dataframe(stock[stock['الكمية'] > 0], use_container_width=True)

    # --- 4. كشف الحساب ---
    with tabs[3]:
        st.subheader("💰 ملخص الكميات لكل منزل")
        if not df.empty:
            pivot = df.pivot_table(index='المنزل', columns='الحالة', values='الكمية', aggfunc='sum', fill_value=0)
            st.dataframe(pivot, use_container_width=True)

    # --- 5. السجل (History) - التعديل المباشر والتصفير ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات (تعديل مباشر + سحب أفقي)")
        if not df.empty:
            # عرض الجدول مع السماح بتعديل الكمية فقط
            history_display = df.iloc[::-1].head(100).copy()
            
            edited_df = st.data_editor(
                history_display,
                column_config={
                    "الكمية": st.column_config.NumberColumn("🔢 الكمية", width="small", required=True),
                    "المنزل": st.column_config.TextColumn("🏠 المنزل", width="medium", disabled=True),
                    "المنتج": st.column_config.TextColumn("📦 المنتج", width="medium", disabled=True),
                    "الحالة": st.column_config.TextColumn("📍 الحالة", width="small", disabled=True),
                    "التاريخ": st.column_config.TextColumn("📅 التاريخ", width="medium", disabled=True),
                },
                hide_index=True,
                use_container_width=False, # هذا يسمح بالسحب الأفقي
                key="history_editor"
            )
            
            if st.button("💾 حفظ التعديلات في الإكسل"):
                s = get_sheet()
                # إعادة كتابة البيانات المعدلة في الإكسل
                full_df = df.copy()
                full_df.iloc[edited_df.index] = edited_df
                s.update([full_df.columns.values.tolist()] + full_df.values.tolist())
                st.success("تم الحفظ!")
                st.cache_resource.clear()
                st.rerun()

            st.divider()
            # زر تصفير سريع
            st.subheader("❌ تصفير سريع لعملية")
            idx = st.selectbox("اختر سطر لتصفيره", options=history_display.index, 
                               format_func=lambda x: f"{history_display.loc[x, 'المنزل']} - {history_display.loc[x, 'المنتج']}")
            if st.button("تصفير السطر المختار ✓"):
                target = history_display.loc[idx]
                save_new_row([target['الكمية'], target['المنتج'], target['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                st.rerun()

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
