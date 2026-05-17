import streamlit as st
import pandas as pd
import requests
from io import StringIO
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="ورشة Bébé Sympa", page_icon="🏗️", layout="centered")
st.markdown("<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)

sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"

# جلب بيانات السلع
@st.cache_data(ttl=60)
def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
    r = requests.get(url, timeout=10)
    return pd.read_csv(StringIO(r.text))

# جلب بيانات الكراس والسلع
df_karas = load_sheet("الكراس")
df_sila3 = load_sheet("السلع")

# قائمة المنازل (أسماء العمال)
منازل = [
    "بباز عيسى", "ڤمغار محمد", "قبايلي خضير", "نعلوفي عيسى",
    "لالوة محمد", "ببايا توفيق", "أداود يحيى", "أداود عبد الرحمان",
    "أداود عمر", "بضليس فارس", "بضليس يوسف", "كيوكيو محمد",
    "سيوسيو نور الدين", "حجاج رستم", "باباحني يوسف", "باباحني خضير"
]

# تهيئة سجل العمليات
if "operations" not in st.session_state:
    st.session_state.operations = []

st.divider()

# ── واجهة الإخراج
st.markdown("### 📤 تسجيل إخراج")

col1, col2 = st.columns(2)

with col1:
    # قائمة المنتجات من ورقة الكراس
    produits = df_karas["Référence"].dropna().tolist()
    produit = st.selectbox("المنتج", produits)

with col2:
    quantite = st.number_input("الكمية", min_value=1, step=1)

col3, col4 = st.columns(2)

with col3:
    type_op = st.selectbox("النوع", ["CT (خياطة)", "FN (تغليف)"])

with col4:
    nom = st.selectbox("المنزل", منازل)

if st.button("✅ تأكيد الإخراج", use_container_width=True):
    op = {
        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "المنتج": produit,
        "الكمية": quantite,
        "النوع": type_op,
        "المنزل": nom,
        "الاتجاه": "CT → FN" if "CT" in type_op else "FN → مخزن"
    }
    st.session_state.operations.append(op)
    st.success(f"✅ تم تسجيل إخراج {quantite} من {produit} إلى {nom}")

st.divider()

# ── عرض العمليات المسجلة
st.markdown("### 📋 سجل العمليات")

if st.session_state.operations:
    df_ops = pd.DataFrame(st.session_state.operations)
    st.dataframe(df_ops, use_container_width=True)
    
    # تحميل كـ CSV
    csv = df_ops.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل السجل CSV", csv, "سجل_العمليات.csv", "text/csv")
else:
    st.info("لا توجد عمليات مسجلة بعد.")

st.divider()

# ── عرض جدول الكراس
st.markdown("### 📦 جدول الكراس الحالي")
st.dataframe(df_karas, use_container_width=True)
