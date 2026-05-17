import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة والعناوين
st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", page_icon="🏗️", layout="centered")

# رابط الجدول الخاص بك مباشرة بدون حاجة لتعديله
SHEET_URL = "https://docs.google.com/spreadsheets/d/1B6f0_W0Z7yUwa-N0mKkVA_mKkvWp1_7k-xkvaawpw9M/edit?usp=sharing"

# 2. دالة جلب البيانات من Google Sheets
@st.cache_data(ttl=60)  # تحديث البيانات تلقائيًا كل دقيقة
def get_sheet_data(sheet_name):
    base_url = SHEET_URL.split("/edit")[0]
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(csv_url)

# --- شاشة النظام الرئيسية مباشرة ---
st.markdown(f"<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)
st.write("مرحباً بك! تم تحميل بيانات الورشة مباشرة من جدول البيانات.")

# جلب وعرض بيانات ورقة "السلع"
st.markdown("### 📦 جدول السلع والمخزون الحالي")
with st.spinner("جاري تحديث جدول السلع من Google Sheets..."):
    try:
        df_goods = get_sheet_data("السلع")
        
        # عرض جدول السلع بشكل منسق وجذاب
        st.dataframe(df_goods, use_container_width=True)
        
        # إحصائية بسيطة
        st.info(f"إجمالي عدد المواد والسلع المسجلة حالياً: {len(df_goods)} صنف.")
        
    except Exception as e:
        st.error("⚠️ تعذر الاتصال بجدول البيانات أو تحميل ورقة السلع.")
        st.info("تأكد فقط من أن خيار المشاركة (Share) في ملف الـ Google Sheets مضبوط على 'أي شخص لديه الرابط يمكنه العرض'.")
        
