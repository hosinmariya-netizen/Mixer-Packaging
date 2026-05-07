import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="نظام Bébé Sympa الملون", page_icon="🟢", layout="wide")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق الليلي مع إضافة ألوان الحالات
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.9)), url("{logo_path}");
        background-attachment: fixed; background-size: 350px; background-position: center; background-repeat: no-repeat;
    }}
    .main {{ text-align: right; direction: rtl; }}
    h1, h2, h3, p, span, label {{ color: #ffffff !important; text-align: right; }}
    
    /* تنسيق الأزرار */
    div.stButton > button {{ border-radius: 20px; background-color: #00a4e4; color: white; font-weight: bold; }}
    
    /* تحسين شكل الجدول */
    .stDataFrame {{ background-color: rgba(0,0,0,0.3); border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# --- القائمة الجانبية ---
st.sidebar.image(logo_path, width=150)
user_password = st.sidebar.text_input("أدخل كلمة السر", type="password")

if user_password == "2025":
    st.sidebar.divider()
    st.sidebar.subheader("➕ إضافة سريعة")
    with st.sidebar.form("new_entry"):
        p_name = st.text_input("اسم المنتج")
        p_type = st.selectbox("نوع العملية", ["ct (خياطة)", "fn (تغليف)"])
        submit = st.form_submit_button("تسجيل")
        
        if submit and p_name:
            df_existing = conn.read(ttl=0)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            # استخراج الكود فقط (ct أو fn)
            code = "ct" if "ct" in p_type else "fn"
            new_row = pd.DataFrame([{"المنتج": p_name, "الحالة": code, "تاريخ_التحديث": now}])
            updated_df = pd.concat([df_existing, new_row], ignore_index=True).fillna("-")
            conn.update(data=updated_df)
            st.sidebar.success(f"تمت إضافة {code} بنجاح")
            st.rerun()

if user_password != "2025":
    st.title("🌙 نظام Bébé Sympa")
    st.info("أدخل كلمة السر للبدء")
    st.stop()

# --- الواجهة الرئيسية ---
col1, col2 = st.columns([4, 1])
with col1: st.title("📊 لوحة المراقبة الذكية")
with col2:
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.rerun()

try:
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()

    # --- وظيفة التلوين التلقائي ---
    def color_status(val):
        if str(val).lower() == 'ct':
            return 'background-color: #1e3a8a; color: white;' # أزرق داكن للخياطة
        elif str(val).lower() == 'fn':
            return 'background-color: #7f1d1d; color: white;' # أحمر داكن للتغليف
        return ''

    st.header("🔎 البحث والفلترة")
    search = st.text_input("ابحث عن منتج أو كود (ct/fn)...")
    
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]

    # عرض الجدول مع تطبيق الألوان على عمود "الحالة"
    if 'الحالة' in df.columns:
        st.dataframe(df.style.applymap(color_status, subset=['الحالة']), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    # --- إحصائيات الأكواد ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("📦 الإجمالي", len(df))
    if 'الحالة' in df.columns:
        m2.metric("🧵 الخياطة (ct)", len(df[df['الحالة'].str.contains('ct', case=False, na=False)]))
        m3.metric("🎁 التغليف (fn)", len(df[df['الحالة'].str.contains('fn', case=False, na=False)]))

except Exception as e:
    st.error("تأكد من وجود عمود باسم 'الحالة' في جوجل شيت")
    
