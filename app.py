import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Bébé Sympa", layout="wide")

# تصميم CSS بسيط لضمان اتجاه النص ولون الهيدر
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    /* تخصيص شكل جدول البيانات */
    [data-testid="stTable"] { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# 2. الدوال البرمجية للربط بـ Google Sheets
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
    if s:
        df = pd.DataFrame(s.get_all_records())
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

# 3. بناء واجهة المستخدم
try:
    df = get_data()
    
    col_t, col_btn = st.columns([4, 1])
    col_t.title("🛡️ نظام الرقابة الذكي")
    if col_btn.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.rerun()

    tabs = st.tabs(["📊 الملخص", "📜 السجل (تعديل مباشر)"])

    # --- تبويب السجل (History) ---
    with tabs[1]:
        st.subheader("سجل العمليات")
        st.info("💡 يمكنك سحب الجدول لليسار، وتعديل الكمية مباشرة من الخانة.")

        if not df.empty:
            # ترتيب البيانات: الأحدث أولاً
            df_display = df.iloc[::-1].copy()
            
            # استخدام محرر البيانات الاحترافي (يضمن بقاء الجدول أفقياً)
            edited_df = st.data_editor(
                df_display,
                column_config={
                    "الكمية": st.column_config.NumberColumn("الكمية", width="medium", min_value=0),
                    "التاريخ": st.column_config.TextColumn("التاريخ", width="large"),
                    "الحالة": st.column_config.TextColumn("الحالة", width="small"),
                },
                disabled=["المنتج", "المنزل", "التاريخ", "الحالة"], # قفل الخانات الأخرى
                hide_index=True,
                use_container_width=True,
                key="data_editor"
            )

            # زر الحفظ (عند تغيير أي كمية)
            if st.button("💾 حفظ التعديلات في الإكسل"):
                s = get_sheet()
                # إعادة البيانات لأصلها (بدون قلب) وتحديثها
                df_to_save = edited_df.iloc[::-1]
                s.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
                st.success("تم تحديث البيانات بنجاح!")
                st.cache_resource.clear()
                st.rerun()
        
    # --- تبويب الملخص ---
    with tabs[0]:
        if not df.empty:
            st.write("📈 إجمالي الكميات لكل منزل:")
            summary = df.groupby(['المنزل', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
            st.dataframe(summary, use_container_width=True)

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
