import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
from urllib.parse import quote
from datetime import datetime, date

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
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_spreadsheet():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(sheet_id)

def get_worksheet(name):
    return get_spreadsheet().worksheet(name)

def get_or_create_worksheet(name, headers):
    try:
        return get_worksheet(name)
    except:
        ss = get_spreadsheet()
        ws = ss.add_worksheet(title=name, rows=1000, cols=20)
        ws.append_row(headers)
        return ws

@st.cache_data(ttl=30)
def load_sheet_csv(name):
    url = "https://docs.google.com/spreadsheets/d/" + sheet_id + "/gviz/tq?tqx=out:csv&sheet=" + quote(name)
    r = requests.get(url, timeout=10)
    return pd.read_csv(StringIO(r.text))

@st.cache_data(ttl=60)
def load_produits(): 
    df = load_sheet_csv("الكراس")
    return df["Référence"].dropna().tolist()

@st.cache_data(ttl=60)
def load_types():
    df = load_sheet_csv("الكراس")
    return [c.strip() for c in df.columns[1:] if c.strip()] or ["FN", "CT"]

@st.cache_data(ttl=60)
def load_منازل():
    df = load_sheet_csv("السلع")
    col = df.iloc[:, 0].dropna()
    return col[col.str.strip() != ""].tolist()

# ── باقي الدوال (load_operations, save_operation, delete_operation, load_ventes, etc.)
@st.cache_data(ttl=30)
def load_operations():
    try:
        ws = get_worksheet("History")
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        df = pd.DataFrame(data[1:], columns=data[0])
        df["الكمية"] = pd.to_numeric(df["الكمية"], errors="coerce").fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

def save_operation(tar, naw, manzil, montaj, sinf, kamia, sajil):
    try:
        ws = get_worksheet("History")
        if not ws.get_all_values():
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        ws.append_row([tar, naw, manzil, montaj, sinf, int(kamia), sajil])
        load_operations.clear()
        return True
    except Exception as e:
        st.warning("خطأ في الحفظ: " + str(e))
        return False

def delete_operation(row_idx):
    try:
        ws = get_worksheet("History")
        ws.delete_rows(row_idx + 2)
        load_operations.clear()
        return True
    except Exception as e:
        st.warning(str(e))
        return False

# (load_ventes, save_vente, delete_vente, load_livraisons, save_livraison, cancel_livraison) كما هي في الكود الأصلي
# ... (انسخ باقي الدوال من كودك الأصلي)

# ── تحميل البيانات الأساسية
produits = load_produits()
manazil = load_منازل()
types = load_types()

if st.button("🔄 تحديث جميع البيانات", use_container_width=True):
    for fn in [load_produits, load_types, load_منازل, load_operations, load_ventes, load_livraisons]:
        fn.clear()
    st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📤 إخراج", "📥 استلام", "🛒 البيع", "🏪 المخزن", "❌ الأخطاء",
    "📦 No Livraison", "🖼️ الصور", "📊 History", "📝 الملاحظات"
])

# ── تبويب إخراج (مثال - أكمل باقي الأتبويب بنفس الطريقة)
with tab1:
    st.markdown("### 📤 إخراج إلى المنزل")
    col1, col2 = st.columns(2)
    with col1: produit_out = st.selectbox("المنتج", produits, key="out_prod")
    with col2: quantite_out = st.number_input("الكمية", min_value=1, step=1, key="out_qty")
    col3, col4 = st.columns(2)
    with col3: type_out = st.selectbox("النوع", types, key="out_type")
    with col4: nom_out = st.selectbox("المنزل", manazil, key="out_nom")
    
    date_out = st.date_input("التاريخ", value=date.today(), key="out_date")
    time_out = st.time_input("الوقت", value=datetime.now().time(), key="out_time")
    
    if st.button("✅ تأكيد الإخراج", use_container_width=True):
        tar = datetime.combine(date_out, time_out).strftime("%Y-%m-%d %H:%M")
        sijil = f"{nom_out} / {produit_out}/{type_out}/{quantite_out}"
        if save_operation(tar, "إخراج", nom_out, produit_out, type_out, quantite_out, sijil):
            st.success("تم الإخراج بنجاح")

# ── تبويب No Livraison (مُصحح)
with tab6:
    st.markdown("### 📦 No Livraison")
    col1, col2 = st.columns(2)
    with col1:
        liv_prod = st.selectbox("المنتج", produits, key="liv_prod")
    with col2:
        liv_qty = st.number_input("الكمية المطلوبة", min_value=1, step=1, key="liv_qty")
    
    if st.button("➕ إضافة الطلبية", use_container_width=True):
        if save_livraison(liv_prod, liv_qty):
            st.success(f"تمت إضافة طلبية {liv_prod}")
            st.rerun()

    st.divider()
    livs = load_livraisons()
    if not livs:
        st.info("لا توجد طلبيات نشطة")
    else:
        for liv in livs:
            c1, c2, c3 = st.columns([4, 3, 2])
            with c1:
                st.write(f"**{liv['المنتج']}**")
            with c2:
                st.write(f"مطلوب: **{liv['الكمية المطلوبة']}** | في الإنتاج: {liv['في الإنتاج']}")
            with c3:
                if st.button("❌ إلغاء", key=f"cancel_liv_{liv['row_idx']}"):
                    cancel_livraison(liv['row_idx'])
                    st.rerun()

st.caption("Baby Sympa © 2026")
