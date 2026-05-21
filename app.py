import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
from urllib.parse import quote
from datetime import datetime, date
import base64

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
div[data-baseweb="select"] input {
    caret-color: transparent !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center'>🧸 Baby Sympa</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#ccc'>لوحة تحكم ورشة الخياطة</h4>", unsafe_allow_html=True)

sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"
BASE_IMAGE_URL = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images/"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds).open_by_key(sheet_id)

def get_worksheet(name):
    return get_spreadsheet().worksheet(name)

def get_or_create_worksheet(name, headers):
    try:
        return get_worksheet(name)
    except Exception:
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

@st.cache_data(ttl=30)
def load_operations():
    try:
        ws = get_worksheet("History")
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        df = pd.DataFrame(data[1:], columns=data[0])
        df["الكمية"] = pd.to_numeric(df["الكمية"], errors="coerce").fillna(0).astype(int)
        return df
    except Exception:
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

# باقي الدوال (load_ventes, save_vente, delete_vente, load_livraisons ... إلخ) كاملة كما هي

# (للاختصار هنا، انسخ باقي الكود من عندك بعد الدالة delete_operation، وخلي غير نسخة واحدة)

# ── باقي الكود (التبويبات، الـ functions، كلشي) مرة واحدة فقط
# ... (انسخ الجزء الثاني من كودك الأصلي بدون تكرار import والـ st.set_page_config)

produits = load_produits()
manazil = load_منازل()
types = load_types()

if st.button("🔄 تحديث جميع البيانات", use_container_width=True):
    for fn in [load_produits, load_types, load_منازل, load_operations, load_ventes, load_livraisons, load_images, load_sheet_csv, load_notes]:
        fn.clear()
    st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📤 إخراج", "📥 استلام", "🛒 البيع", "🏪 المخزن", "❌ الأخطاء",
    "📦 No Livraison", "🖼️ الصور", "📊 History", "📝 الملاحظات"
])

# هنا ضع باقي with tab1: ... with tab9: ... (مرة واحدة فقط)
