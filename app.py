import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
from urllib.parse import quote

st.set_page_config(page_title="Baby Sympa", page_icon="🧸", layout="centered")

# --- CSS التنسيق ---
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
[data-testid="stMain"] > div { position: relative; z-index: 1; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:white'>🧸 Baby Sympa</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#ccc'>لوحة تحكم ورشة الخياطة</h4>", unsafe_allow_html=True)

# --- الإعدادات ---
sheet_id = "1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_spreadsheet():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(sheet_id)

def get_worksheet(name):
    return get_spreadsheet().worksheet(name)

# --- دوال البيانات ---
@st.cache_data(ttl=30)
def load_sheet_csv(name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
    r = requests.get(url, timeout=10)
    return pd.read_csv(StringIO(r.text))

# تحميل القوائم الأساسية
produits = load_sheet_csv("الكراس")["Référence"].dropna().tolist()

@st.cache_data(ttl=30)
def load_livraisons():
    try:
        ws = get_worksheet("No Livrai")
        data = ws.get_all_values()
        if len(data) <= 1: return []
        livs = []
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 4 and str(row[3]).strip() == "نشط":
                livs.append({
                    "row_idx": i,
                    "المنتج": row[0],
                    "الكمية المطلوبة": int(row[1]) if str(row[1]).isdigit() else 0
                })
        return livs
    except: return []

def save_livraison(montaj, kamia):
    ws = get_worksheet("No Livrai")
    ws.append_row([montaj, int(kamia), 0, "نشط"])
    return True

def cancel_livraison(row_idx):
    ws = get_worksheet("No Livrai")
    ws.update_cell(row_idx, 4, "ملغى")
    return True

# --- واجهة المستخدم ---
if st.button("🔄 تحديث البيانات", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

tab6 = st.tabs(["📦 No Livraison"])[0] # يمكنك إضافة باقي التابات هنا

with tab6:
    st.markdown("### 📦 إضافة طلبية جديدة")
    col1, col2 = st.columns(2)
    with col1: liv_prod = st.selectbox("المنتج", produits)
    with col2: liv_qty = st.number_input("الكمية المطلوبة", min_value=1, step=1)
    
    if st.button("➕ إضافة الطلبية"):
        if save_livraison(liv_prod, liv_qty):
            st.success("✅ تمت الإضافة")
            st.cache_data.clear()
            st.rerun()

    st.divider()
    st.markdown("#### الطلبيات النشطة")
    livs = load_livraisons()
    if not livs:
        st.info("لا توجد طلبيات نشطة")
    else:
        for liv in livs:
            cols = st.columns([4, 2, 2])
            cols[0].write(f"**{liv['المنتج']}**")
            cols[1].write(f"الكمية: {liv['الكمية المطلوبة']}")
            if cols[2].button("❌ إلغاء", key=f"del_{liv['row_idx']}"):
                cancel_livraison(liv['row_idx'])
                st.cache_data.clear()
                st.rerun()
