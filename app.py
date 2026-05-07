import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa الذكي", layout="wide")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق الليلي
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("{logo_path}");
        background-attachment: fixed; background-size: 350px; background-position: center; background-repeat: no-repeat;
    }}
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; text-align: right; }}
    div.stButton > button {{ border-radius: 20px; background-color: #00a4e4; color: white; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# --- القائمة الجانبية ---
st.sidebar.image(logo_path, width=150)
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password == "2025":
    st.sidebar.divider()
    st.sidebar.header("📝 تسجيل طلبية جديدة")
    # هنا تكمن الفكرة: البرنامج يأخذ التاريخ تلقائياً
    with st.sidebar.form("new_order"):
        prod_name = st.text_input("اسم المنتج")
        ws_name = st.text_input("ورشة الخياطة")
        submit_order = st.form_submit_button("إرسال وحفظ التاريخ تلقائياً")
        
        if submit_order and prod_name and ws_name:
            # جلب البيانات الحالية
            existing_data = conn.read(ttl=0)
            # إنشاء سطر جديد مع التاريخ والوقت الحالي تلقائياً
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entry = pd.DataFrame([{
                "المنتج": prod_name,
                "ورشة_الخياطة": ws_name,
                "تاريخ_الخروج_للخياطة": now, # التاريخ أُخذ آلياً هنا
                "الحالة": "في الخياطة"
            }])
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True).fillna("-")
            conn.update(data=updated_df)
            st.sidebar.success("تم التسجيل مع التاريخ آلياً!")
            st.rerun()

# --- واجهة العرض الرئيسية ---
if user_password != "2025":
    st.warning("يرجى إدخال كلمة السر")
    st.stop()

col_title, col_refresh = st.columns([4, 1])
with col_title: st.title("📊 لوحة الإنتاج الذكية")
with col_refresh:
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()
    st.header("🔎 البحث")
    search = st.text_input("ابحث هنا...")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, na=False)).any(axis=1)]
    st.dataframe(df, use_container_width=True)
except:
    st.error("تأكد من عناوين الجدول في جوجل شيت")
    
