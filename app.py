import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# الاتصال بجوجل شيت
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

# الواجهة
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز"])

    # --- TAB 5: السجل (History) ---
    with tabs[4]:
        st.subheader("📜 سجل المعاملات (History)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50)
            for i, row in history_df.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1, 1, 2])
                c1.write(row['المنزل'])
                c2.write(row['المنتج'])
                c3.write(row['الحالة'])
                # تعديل الكمية مع تأكيد
                new_qty = c4.number_input("الكمية", value=int(row['الكمية']), key=f"qty_{i}")
                if c5.button("تعديل", key=f"edit_{i}"):
                    st.warning(f"هل أنت متأكد من تعديل الكمية من {int(row['الكمية'])} إلى {new_qty}؟")
                    if st.button("✅ تأكيد", key=f"confirm_{i}"):
                        append_row([new_qty, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), row['الحالة']])
                        st.cache_resource.clear()
                        st.session_state.df = get_data()
                        st.success("✅ تم تعديل الكمية بنجاح")
                        st.rerun()
        else:
            st.info("السجل فارغ حالياً.")

    # --- TAB 6: إنجاز ---
    with tabs[5]:
        st.subheader("✅ إنجاز المنازل")
        if not df.empty:
            summary = df.groupby("المنزل").agg(
                عدد_المنتجات=("المنتج", "nunique"),
                مجموع_الكمية=("الكمية", "sum")
            ).reset_index()
            summary["مجموع_الكمية"] = summary["مجموع_الكمية"].astype(int)  # بدون فاصلة

            def highlight_row(row):
                return ['background-color: red; color: white;' if row['مجموع_الكمية'] == 0 else '' for _ in row]

            st.dataframe(
                summary.style.apply(highlight_row, axis=1),
                use_container_width=True
            )
        else:
            st.info("لا توجد بيانات حالياً.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
