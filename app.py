import streamlit as st
import pandas as pd
import requests
from io import StringIO
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="ورشة Bébé Sympa", page_icon="🏗️", layout="centered")
st.markdown("<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)

sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"

@st.cache_data(ttl=60)
def load_sheet(name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
    r = requests.get(url, timeout=10)
    return pd.read_csv(StringIO(r.text))

df_karas = load_sheet("الكراس")

منازل = [
    "بباز عيسى", "ڤمغار محمد", "قبايلي خضير", "نعلوفي عيسى",
    "لالوة محمد", "ببايا توفيق", "أداود يحيى", "أداود عبد الرحمان",
    "أداود عمر", "بضليس فارس", "بضليس يوسف", "كيوكيو محمد",
    "سيوسيو نور الدين", "حجاج رستم", "باباحني يوسف", "باباحني خضير"
]

if "operations" not in st.session_state:
    st.session_state.operations = []

# ── واجهة الإخراج
st.markdown("### 📤 تسجيل إخراج")

col1, col2 = st.columns(2)
with col1:
    produits = df_karas["Référence"].dropna().tolist()
    produit = st.selectbox("المنتج", produits)
with col2:
    quantite = st.number_input("الكمية", min_value=1, step=1)

col3, col4 = st.columns(2)
with col3:
    type_op = st.selectbox("النوع", ["FN", "CT"])
with col4:
    nom = st.selectbox("المنزل", منازل)

# معاينة الكتابة
st.info(f"📝 سيُكتب هكذا: **{produit}/{quantite}/{type_op}/{nom}**")

if st.button("✅ تأكيد الإخراج", use_container_width=True):
    op = {
        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "المنتج": produit,
        "الكمية": quantite,
        "النوع": type_op,
        "المنزل": nom,
        "السجل": f"{produit}/{quantite}/{type_op}/{nom}",
        "الاتجاه": "CT → FN" if type_op == "CT" else "FN → مخزن"
    }
    st.session_state.operations.append(op)
    st.success(f"✅ تم: {produit}/{quantite}/{type_op}/{nom}")

st.divider()

# ── المخزن مع البحث
st.markdown("### 🏪 المخزن")

if st.session_state.operations:
    df_ops = pd.DataFrame(st.session_state.operations)

    # خانتا البحث
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_منزل = st.text_input("🔍 بحث باسم المنزل")
    with col_s2:
        search_منتج = st.text_input("🔍 بحث باسم المنتج")

    df_filtered = df_ops.copy()
    if search_منزل:
        df_filtered = df_filtered[df_filtered["المنزل"].str.contains(search_منزل, na=False)]
    if search_منتج:
        df_filtered = df_filtered[df_filtered["المنتج"].str.contains(search_منتج, na=False)]

    # عرض المخزن: المنتج + الكمية + النوع
    df_makhzan = df_filtered[["المنتج", "الكمية", "النوع", "المنزل", "التاريخ", "الاتجاه"]]
    st.dataframe(df_makhzan, use_container_width=True)

    # ملخص المخزن
    st.markdown("#### 📊 ملخص المخزن")
    df_summary = df_ops.groupby(["المنتج", "النوع"])["الكمية"].sum().reset_index()
    df_summary.columns = ["المنتج", "النوع", "إجمالي الكمية"]
    st.dataframe(df_summary, use_container_width=True)

    csv = df_ops.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل السجل CSV", csv, "سجل_العمليات.csv", "text/csv")

else:
    st.info("المخزن فارغ — سجّل أول عملية إخراج.")

st.divider()

# ── جدول الكراس
st.markdown("### 📋 جدول الكراس")
st.dataframe(df_karas, use_container_width=True)
