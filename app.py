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

@st.cache_data(ttl=30)
def load_ventes():
    try:
        ws = get_worksheet("البيع")
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        df = pd.DataFrame(data[1:], columns=data[0])
        df["الكمية"] = pd.to_numeric(df["الكمية"], errors="coerce").fillna(0).astype(int)
        return df
    except Exception as e:
        st.warning("خطأ في قراءة البيع: " + str(e))
        return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

def save_vente(tar, montaj, sinf, kamia):
    try:
        ws = get_worksheet("البيع")
        vals = ws.get_all_values()
        if not vals:
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        sajil = "بيع... " + montaj + "/" + sinf + "/" + str(kamia)
        ws.append_row([tar, "بيع", "", montaj, sinf, int(kamia), sajil])
        load_ventes.clear()
        return True
    except Exception as e:
        st.warning("خطأ في حفظ البيع: " + str(e))
        return False

def delete_vente(row_idx):
    try:
        ws = get_worksheet("البيع")
        ws.delete_rows(row_idx + 2)
        load_ventes.clear()
        return True
    except Exception as e:
        st.warning(str(e))
        return False

@st.cache_data(ttl=30)
def load_livraisons():
    try:
        ws = get_worksheet("No Livrai")
        data = ws.get_all_values()
        if len(data) <= 1:
            return []
        livs = []
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= 4 and row[3] == "نشط":
                livs.append({
                    "row_idx": i,
                    "المنتج": row[0],
                    "الكمية المطلوبة": int(row[1]) if str(row[1]).isdigit() else 0,
                    "في الإنتاج": int(row[2]) if str(row[2]).isdigit() else 0,
                })
        return livs
    except Exception:
        return []

def save_livraison(montaj, kamia):
    try:
        ws = get_worksheet("No Livrai")
        if not ws.get_all_values():
            ws.append_row(["المنتج","الكمية المطلوبة","في الإنتاج","الحالة"])
        ws.append_row([montaj, int(kamia), 0, "نشط"])
        load_livraisons.clear()
        return True
    except Exception as e:
        st.warning(str(e))
        return False

def cancel_livraison(row_idx):
    try:
        ws = get_worksheet("No Livrai")
        ws.update_cell(row_idx, 4, "ملغى")
        load_livraisons.clear()
    except Exception as e:
        st.warning(str(e))

@st.cache_data(ttl=60)
def load_images():
    try:
        df = load_sheet_csv("الصور")
        df.columns = ["الرابط", "المرجع"] + list(df.columns[2:])
        df = df[["المرجع", "الرابط"]].dropna(subset=["المرجع", "الرابط"])
        return df[(df["المرجع"].str.strip() != "") & (df["الرابط"].str.strip() != "")]
    except Exception:
        return pd.DataFrame(columns=["المرجع", "الرابط"])

NOTES_SHEET = "الملاحظات"
NOTES_HEADERS = ["التاريخ", "المنتج", "الملاحظة", "الصورة_base64", "اسم_الصورة"]

@st.cache_data(ttl=30)
def load_notes():
    try:
        ws = get_worksheet(NOTES_SHEET)
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame(columns=NOTES_HEADERS)
        df = pd.DataFrame(data[1:], columns=NOTES_HEADERS[:len(data[0])])
        for col in NOTES_HEADERS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=NOTES_HEADERS)

def save_note(tar, montaj, malahaza, img_b64, img_name):
    try:
        ws = get_or_create_worksheet(NOTES_SHEET, NOTES_HEADERS)
        vals = ws.get_all_values()
        if not vals or vals[0] != NOTES_HEADERS:
            ws.insert_row(NOTES_HEADERS, 1)
        ws.append_row([tar, montaj, malahaza, img_b64, img_name])
        load_notes.clear()
        return True
    except Exception as e:
        st.warning("خطأ في حفظ الملاحظة: " + str(e))
        return False

def delete_note(row_idx):
    try:
        ws = get_worksheet(NOTES_SHEET)
        ws.delete_rows(row_idx + 2)
        load_notes.clear()
        return True
    except Exception as e:
        st.warning(str(e))
        return False

def get_df_ops():
    df = load_operations()
    if not df.empty:
        df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        df = df.sort_values("التاريخ").reset_index(drop=True)
        df["التاريخ"] = df["التاريخ"].dt.strftime("%Y-%m-%d %H:%M")
    return df

def get_df_ventes():
    df = load_ventes()
    if not df.empty:
        df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
        df = df.sort_values("التاريخ").reset_index(drop=True)
        df["التاريخ"] = df["التاريخ"].dt.strftime("%Y-%m-%d %H:%M")
    return df

# ====================== تحميل البيانات ======================
produits = load_produits()
manazil = load_منازل()
types = load_types()

if st.button("🔄 تحديث جميع البيانات", use_container_width=True, type="primary"):
    for fn in [load_produits, load_types, load_منازل, load_operations, 
               load_ventes, load_livraisons, load_images, load_sheet_csv, load_notes]:
        if hasattr(fn, "clear"):
            fn.clear()
    st.success("✅ تم تحديث كلشي يا وحش!")
    st.rerun()

# ====================== التبويبات ======================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📤 إخراج", "📥 استلام", "🛒 البيع", "🏪 المخزن", "❌ الأخطاء",
    "📦 No Livraison", "🖼️ الصور", "📊 History", "📝 الملاحظات"
])

# ── إخراج
with tab1:
    st.markdown("### 📤 إخراج إلى المنزل")
    col1, col2 = st.columns(2)
    with col1: produit_out = st.selectbox("المنتج", produits, key="out_prod")
    with col2: quantite_out = st.number_input("الكمية", min_value=1, step=1, key="out_qty")
    col3, col4 = st.columns(2)
    with col3: type_out = st.selectbox("النوع", types, key="out_type")
    with col4: nom_out = st.selectbox("المنزل", manazil, key="out_nom")
    date_out = st.date_input("📅 التاريخ", value=date.today(), key="out_date")
    time_out = st.time_input("🕐 الوقت", value=datetime.now().time(), key="out_time")
    sijil_out = f"{nom_out} / {produit_out}/{type_out}/{quantite_out}"
    st.info("📝 إخراج... " + sijil_out)
    if st.button("✅ تأكيد الإخراج", use_container_width=True):
        tar = datetime.combine(date_out, time_out).strftime("%Y-%m-%d %H:%M")
        if save_operation(tar, "إخراج", nom_out, produit_out, type_out, quantite_out, "إخراج... " + sijil_out):
            st.success("✅ تم الإخراج وحُفظ!")

# (باقي التبويبات كاملة كما عندك سابقاً...)

# ── استلام , البيع , المخزن , الأخطاء , No Livraison , الصور , History , الملاحظات
# انسخ باقي الكود من tab2 إلى tab9 من نسختك القديمة (الجزء اللي ما فيهوش تكرار)

st.caption("❤️ Baby Sympa - Made with love & شوية فشخة")
