import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - لوحة الألوان", page_icon="🟢", layout="wide")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق العام
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.9)), url("{logo_path}");
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
    st.sidebar.subheader("➕ إضافة جديدة")
    with st.sidebar.form("new_entry"):
        p_name = st.text_input("اسم المنتج")
        p_type = st.selectbox("الحالة", ["ct", "fn"])
        submit = st.form_submit_button("إضافة")
        if submit and p_name:
            df_existing = conn.read(ttl=0)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            new_row = pd.DataFrame([{"المنتج": p_name, "الحالة": p_type, "التاريخ": now}])
            updated_df = pd.concat([df_existing, new_row], ignore_index=True).fillna("-")
            conn.update(data=updated_df)
            st.sidebar.success("تم الحفظ")
            st.rerun()

if user_password != "2025":
    st.stop()

# --- الواجهة الرئيسية ---
col1, col2 = st.columns([4, 1])
with col1: st.title("📊 تتبع الإنتاج بالألوان")
with col2:
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()

    # --- دالة التلوين المحدثة ---
    def apply_color(row):
        color = ''
        status = str(row['الحالة']).strip().lower()
        if status == 'ct':
            color = 'background-color: #005f73; color: white' # أزرق بترولي للخياطة
        elif status == 'fn':
            color = 'background-color: #9b2226; color: white' # أحمر غامق للتغليف
        return [color] * len(row)

    st.header("🔎 البحث")
    search = st.text_input("ابحث هنا...")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]

    # عرض الجدول مع التلوين (تأكد من وجود عمود اسمه 'الحالة')
    if 'الحالة' in df.columns:
        # استخدام style.apply بدلاً من applymap لتلوين الصف بالكامل بناءً على الحالة
        st.dataframe(df.style.apply(apply_color, axis=1), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
        st.warning("تنبيه: يجب أن يكون اسم العمود في جوجل شيت هو 'الحالة' لكي تعمل الألوان.")

except Exception as e:
    st.error(f"خطأ: {e}")
