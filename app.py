import streamlit as st
import pandas as pd
import requests
from io import StringIO
from urllib.parse import quote
from datetime import datetime

st.set_page_config(page_title="Baby Sympa", page_icon="🧸", layout="centered")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://raw.githubusercontent.com/hosinmariya-/mixer-packaging/main/images%20(5)%20(5).jpeg");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.83);
    z-index: 0;
}
[data-testid="stMain"] > div {
    position: relative;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center'>🧸 Baby Sympa</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#ccc'>لوحة تحكم ورشة الخياطة</h4>", unsafe_allow_html=True)

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

def get_df_ops():
    if st.session_state.operations:
        return pd.DataFrame(st.session_state.operations)
    return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

produits = df_karas["Référence"].dropna().tolist()

tab1, tab2, tab3, tab4 = st.tabs(["📤 إخراج", "📥 استلام", "🏪 المخزن", "❌ الأخطاء"])

# ── إخراج
with tab1:
    st.markdown("### 📤 إخراج إلى المنزل")
    col1, col2 = st.columns(2)
    with col1:
        produit_out = st.selectbox("المنتج", produits, key="out_prod")
    with col2:
        quantite_out = st.number_input("الكمية", min_value=1, step=1, key="out_qty")
    col3, col4 = st.columns(2)
    with col3:
        type_out = st.selectbox("النوع", ["FN", "CT"], key="out_type")
    with col4:
        nom_out = st.selectbox("المنزل", منازل, key="out_nom")

    sijil_out = f"{nom_out} / {produit_out}/{type_out}/{quantite_out}"
    st.info(f"📝 إخراج... {sijil_out}")

    if st.button("✅ تأكيد الإخراج", use_container_width=True):
        st.session_state.operations.append({
            "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "النوع": "إخراج",
            "المنزل": nom_out,
            "المنتج": produit_out,
            "الصنف": type_out,
            "الكمية": quantite_out,
            "السجل": f"إخراج... {sijil_out}"
        })
        st.success(f"✅ تم الإخراج: {sijil_out}")

# ── استلام
with tab2:
    st.markdown("### 📥 استلام من المنزل")
    col1, col2 = st.columns(2)
    with col1:
        produit_in = st.selectbox("المنتج", produits, key="in_prod")
    with col2:
        quantite_in = st.number_input("الكمية", min_value=1, step=1, key="in_qty")
    col3, col4 = st.columns(2)
    with col3:
        type_in = st.selectbox("النوع", ["FN", "CT"], key="in_type")
    with col4:
        nom_in = st.selectbox("المنزل", منازل, key="in_nom")

    sijil_in = f"{nom_in} / {produit_in}/{type_in}/{quantite_in}"
    st.info(f"📝 استلام... {sijil_in}")

    if st.button("✅ تأكيد الاستلام", use_container_width=True):
        df_ops = get_df_ops()

        # حساب الناقص عند الاستلام
        df_منزل = df_ops[
            (df_ops["المنزل"] == nom_in) &
            (df_ops["المنتج"] == produit_in) &
            (df_ops["الصنف"] == type_in)
        ]
        اخراج = df_منزل[df_منزل["النوع"] == "إخراج"]["الكمية"].sum()
        استلام_سابق = df_منزل[df_منزل["النوع"] == "استلام"]["الكمية"].sum()
        ناقص = اخراج - استلام_سابق - quantite_in

        st.session_state.operations.append({
            "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "النوع": "استلام",
            "المنزل": nom_in,
            "المنتج": produit_in,
            "الصنف": type_in,
            "الكمية": quantite_in,
            "السجل": f"استلام... {sijil_in}"
        })

        # إذا كان هناك ناقص → سجّله في الأخطاء
        if ناقص > 0:
            if "errors" not in st.session_state:
                st.session_state.errors = []
            st.session_state.errors.append({
                "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "المنزل": nom_in,
                "المنتج": produit_in,
                "الصنف": type_in,
                "المُخرَج": int(اخراج - استلام_سابق),
                "المُستلَم": quantite_in,
                "الناقص": int(ناقص)
            })
            st.warning(f"⚠️ تم الاستلام لكن هناك ناقص: {int(ناقص)} قطعة")
        else:
            st.success(f"✅ تم الاستلام: {sijil_in}")

# ── المخزن
with tab3:
    st.markdown("### 🏪 المخزن والبحث")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        search_منزل = st.text_input("🔍 بحث باسم المنزل")
    with col_s2:
        search_منتج = st.text_input("🔍 بحث باسم المنتج")

    df_ops = get_df_ops()
    if not df_ops.empty:
        df_out = df_ops[df_ops["النوع"] == "إخراج"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum()
        df_in  = df_ops[df_ops["النوع"] == "استلام"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum()
        df_balance = (df_out - df_in).fillna(df_out).reset_index()
        df_balance.columns = ["المنزل", "المنتج", "الصنف", "الرصيد المتبقي"]

        if search_منزل:
            df_balance = df_balance[df_balance["المنزل"].str.contains(search_منزل, na=False)]
        if search_منتج:
            df_balance = df_balance[df_balance["المنتج"].str.contains(search_منتج, na=False)]

        st.dataframe(df_balance, use_container_width=True)
        st.divider()
        st.markdown("#### 📜 كل السجلات")
        st.dataframe(df_ops[["التاريخ","النوع","السجل"]], use_container_width=True)

        csv = df_ops.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تحميل CSV", csv, "سجل_العمليات.csv", "text/csv")
    else:
        st.info("المخزن فارغ — سجّل أول عملية.")

# ── الأخطاء
with tab4:
    st.markdown("### ❌ سجل الأخطاء (الناقص فقط)")

    if "errors" not in st.session_state:
        st.session_state.errors = []

    if st.session_state.errors:
        df_errors = pd.DataFrame(st.session_state.errors)
        st.dataframe(df_errors, use_container_width=True)

        # إجمالي الناقص لكل منزل
        st.divider()
        st.markdown("#### 📊 إجمالي الناقص لكل منزل")
        df_total = df_errors.groupby(["المنزل","المنتج","الصنف"])["الناقص"].sum().reset_index()
        df_total.columns = ["المنزل", "المنتج", "الصنف", "إجمالي الناقص"]
        st.dataframe(df_total, use_container_width=True)

        csv_err = df_errors.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تحميل الأخطاء CSV", csv_err, "الأخطاء.csv", "text/csv")
    else:
        st.success("✅ لا توجد أخطاء حتى الآن!")
