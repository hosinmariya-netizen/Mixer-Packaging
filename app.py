import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO, BytesIO
from urllib.parse import quote
from datetime import datetime, date
import base64
from PIL import Image

st.set_page_config(page_title="Baby Sympa", page_icon="🧸", layout="centered")

# ── كلمة السر (تُطلب كل 24 ساعة)
CORRECT_PASSWORD = "2005"

def check_password():
    now = datetime.now()
    last_login = st.session_state.get("last_login")
    if last_login:
        diff = (now - last_login).total_seconds()
        if diff < 86400:
            return True
    st.markdown("""
    <div style='text-align:center; padding:60px 20px'>
        <h1>🧸 Baby Sympa</h1>
        <h4 style='color:#ccc'>لوحة تحكم ورشة الخياطة</h4>
    </div>
    """, unsafe_allow_html=True)
    pwd = st.text_input("🔐 أدخل كلمة السر", type="password", key="pwd_input")
    if st.button("دخول", use_container_width=True):
        if pwd == CORRECT_PASSWORD:
            st.session_state["last_login"] = now
            st.rerun()
        else:
            st.error("❌ كلمة السر غلط!")
    return False

if not check_password():
    st.stop()

# ── أيام الأسبوع بالعربية
ARABIC_DAYS = {
    0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء",
    3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
}

def format_date_arabic(d):
    if isinstance(d, str):
        try:
            d = datetime.strptime(d, "%Y-%m-%d %H:%M")
        except Exception:
            return d
    day_name = ARABIC_DAYS.get(d.weekday(), "")
    return day_name + " " + d.strftime("%d/%m/%y %H:%M")

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
BASE_IMAGE_URL = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images/"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# ── ضغط الصورة لتجنب تجاوز 50000 حرف في Google Sheets
def compress_image_to_b64(img_bytes, max_size=(300, 300), quality=40):
    try:
        img = Image.open(BytesIO(img_bytes))
        img = img.convert("RGB")
        img.thumbnail(max_size, Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")
        # إذا لا زال كبير، نضغط أكثر
        if len(b64) > 40000:
            buffer2 = BytesIO()
            img.thumbnail((200, 200), Image.LANCZOS)
            img.save(buffer2, format="JPEG", quality=25, optimize=True)
            buffer2.seek(0)
            b64 = base64.b64encode(buffer2.read()).decode("utf-8")
        return b64
    except Exception as e:
        st.warning("خطأ في ضغط الصورة: " + str(e))
        return ""

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
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"], value_input_option="RAW")
        ws.append_row([tar, naw, manzil, montaj, sinf, int(kamia), sajil], value_input_option="RAW")
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
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"], value_input_option="RAW")
        sajil = "بيع... " + montaj + "/" + sinf + "/" + str(kamia)
        ws.append_row([tar, "بيع", "", montaj, sinf, int(kamia), sajil], value_input_option="RAW")
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
NOTES_HEADERS = ["التاريخ", "المنتج", "الملاحظة", "الصورة_base64", "اسم_الصورة", "الصوت_base64"]

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

def save_note(tar, montaj, malahaza, img_b64, img_name, audio_b64=""):
    try:
        ws = get_or_create_worksheet(NOTES_SHEET, NOTES_HEADERS)
        vals = ws.get_all_values()
        if not vals or vals[0] != NOTES_HEADERS:
            ws.insert_row(NOTES_HEADERS, 1)
        if len(img_b64) > 40000:
            img_b64 = ""
            img_name = "صورة كبيرة جداً - لم تُحفظ"
        if len(audio_b64) > 40000:
            audio_b64 = ""
        ws.append_row([tar, montaj, malahaza, img_b64, img_name, audio_b64], value_input_option="RAW")
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

def add_manzil(new_name):
    """يضيف اسم منزل جديد في ورقة السلع (العمود A) وورقة الكراس (العمود A)"""
    errors = []
    added_salaa = False
    added_karras = False
    try:
        # ── ورقة السلع: إضافة في العمود A (المنازل)
        ws_salaa = get_worksheet("السلع")
        col_a = ws_salaa.col_values(1)
        # تحقق من التكرار
        existing = [v.strip() for v in col_a if v.strip()]
        if new_name.strip() in existing:
            errors.append("الاسم موجود مسبقاً في السلع")
        else:
            # أضف في أول صف فارغ بعد آخر قيمة في العمود A
            next_row = len(col_a) + 1
            ws_salaa.update_cell(next_row, 1, new_name.strip())
            added_salaa = True
    except Exception as e:
        errors.append("خطأ في السلع: " + str(e))

    try:
        # ── ورقة الكراس: إضافة في العمود A (Référence)
        ws_karras = get_worksheet("الكراس")
        col_a_k = ws_karras.col_values(1)
        existing_k = [v.strip() for v in col_a_k if v.strip()]
        if new_name.strip() in existing_k:
            errors.append("الاسم موجود مسبقاً في الكراس")
        else:
            next_row_k = len(col_a_k) + 1
            ws_karras.update_cell(next_row_k, 1, new_name.strip())
            added_karras = True
    except Exception as e:
        errors.append("خطأ في الكراس: " + str(e))

    if added_salaa or added_karras:
        load_منازل.clear()
        load_sheet_csv.clear()
    return added_salaa, added_karras, errors

def get_df_ops():
    df = load_operations()
    # التاريخ محفوظ كنص عربي — نعرضه مباشرة بدون تحويل
    return df

def get_df_ventes():
    df = load_ventes()
    # التاريخ محفوظ كنص عربي — نعرضه مباشرة بدون تحويل
    return df

def show_records_with_delete(df, tab_key, delete_fn, manazil_list, produits_list):
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        s_manzil = st.text_input("🔍 بحث بالمنزل", key="s_manzil_" + tab_key)
    with col_s2:
        s_montaj = st.text_input("🔍 بحث بالمنتج", key="s_montaj_" + tab_key)
    with col_s3:
        s_tar = st.text_input("📅 بحث بالتاريخ", placeholder="2026-05-19", key="s_tar_" + tab_key)

    if s_manzil:
        sugg = [m for m in manazil_list if s_manzil.strip().lower() in m.lower()]
        if sugg:
            chosen = st.selectbox("📌 اختر:", ["—"] + sugg[:6], key="sugg_m_" + tab_key)
            if chosen != "—":
                s_manzil = chosen
    if s_montaj:
        sugg = [p for p in produits_list if s_montaj.strip().lower() in p.lower()]
        if sugg:
            chosen = st.selectbox("📌 اختر:", ["—"] + sugg[:6], key="sugg_p_" + tab_key)
            if chosen != "—":
                s_montaj = chosen

    df_f = df.copy()
    if s_manzil and s_manzil != "—":
        df_f = df_f[df_f["المنزل"].str.contains(s_manzil, na=False, case=False)]
    if s_montaj and s_montaj != "—":
        df_f = df_f[df_f["المنتج"].str.contains(s_montaj, na=False, case=False)]
    if s_tar:
        df_f = df_f[df_f["التاريخ"].str.contains(s_tar, na=False)]

    if df_f.empty:
        st.info("لا توجد نتائج.")
        return

    for idx, row in df_f.iterrows():
        col_r, col_d = st.columns([5, 1])
        with col_r:
            st.write("**" + str(row["التاريخ"]) + "** | " + str(row.get("النوع","")) + " | " + str(row["المنزل"]) + " | " + str(row["المنتج"]) + " | " + str(row["الصنف"]) + " | " + str(row["الكمية"]))
        with col_d:
            del_key = "del_" + tab_key + "_" + str(idx)
            if st.button("🗑️", key=del_key):
                st.session_state["confirm_" + tab_key + "_" + str(idx)] = True

        conf_key = "confirm_" + tab_key + "_" + str(idx)
        if st.session_state.get(conf_key):
            st.warning("⚠️ راك سور؟")
            c1, c2 = st.columns(2)
            with c1:
                yes_key = "yes_" + tab_key + "_" + str(idx)
                if st.button("✅ تأكيد", key=yes_key, use_container_width=True):
                    delete_fn(idx)
                    st.session_state[conf_key] = False
                    st.rerun()
            with c2:
                no_key = "no_" + tab_key + "_" + str(idx)
                if st.button("❌ إلغاء", key=no_key, use_container_width=True):
                    st.session_state[conf_key] = False
                    st.rerun()

    st.divider()
    csv = df_f.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل CSV", csv, "sajil_" + tab_key + ".csv", "text/csv", key="csv_" + tab_key)


# ── تحميل البيانات
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

# ── إخراج
with tab1:
    st.markdown("### 📤 إخراج إلى المنزل")

    # اختيار المنتج بالبحث النصي + أزرار
    out_search = st.text_input("🔍 اكتب اسم المنتج", key="out_search", placeholder="مثال: Bv1")
    filtered_out = [p for p in produits if out_search.strip().lower() in p.lower()] if out_search.strip() else produits
    if "out_prod_selected" not in st.session_state:
        st.session_state["out_prod_selected"] = produits[0] if produits else ""
    if out_search.strip():
        if filtered_out:
            cols_btn = st.columns(3)
            for i, p in enumerate(filtered_out[:9]):
                with cols_btn[i % 3]:
                    if st.button(p, key="out_btn_" + p, use_container_width=True):
                        st.session_state["out_prod_selected"] = p
                        st.rerun()
        else:
            st.warning("لا يوجد منتج بهذا الاسم")
    produit_out = st.session_state["out_prod_selected"]
    st.info("✅ المنتج المختار: **" + produit_out + "**")

    col2, col3 = st.columns(2)
    with col2:
        quantite_out = st.number_input("الكمية", min_value=1, step=1, key="out_qty")
    with col3:
        type_out = st.selectbox("النوع", types, key="out_type")
    nom_out = st.selectbox("المنزل", manazil, key="out_nom")
    date_out = st.date_input("📅 التاريخ", value=date.today(), key="out_date")
    time_out = st.time_input("🕐 الوقت", value=datetime.now().time(), key="out_time")
    sijil_out = nom_out + " / " + produit_out + "/" + type_out + "/" + str(quantite_out)
    st.info("📝 إخراج... " + sijil_out)
    if st.button("✅ تأكيد الإخراج", use_container_width=True):
        tar = format_date_arabic(datetime.combine(date_out, time_out))
        if save_operation(tar, "إخراج", nom_out, produit_out, type_out, quantite_out, "إخراج... " + sijil_out):
            st.success("✅ تم الإخراج وحُفظ: " + sijil_out)

# ── استلام
with tab2:
    st.markdown("### 📥 استلام من المنزل")

    in_search = st.text_input("🔍 اكتب اسم المنتج", key="in_search", placeholder="مثال: Bv1")
    filtered_in = [p for p in produits if in_search.strip().lower() in p.lower()] if in_search.strip() else produits
    if "in_prod_selected" not in st.session_state:
        st.session_state["in_prod_selected"] = produits[0] if produits else ""
    if in_search.strip():
        if filtered_in:
            cols_btn = st.columns(3)
            for i, p in enumerate(filtered_in[:9]):
                with cols_btn[i % 3]:
                    if st.button(p, key="in_btn_" + p, use_container_width=True):
                        st.session_state["in_prod_selected"] = p
                        st.rerun()
        else:
            st.warning("لا يوجد منتج بهذا الاسم")
    produit_in = st.session_state["in_prod_selected"]
    st.info("✅ المنتج المختار: **" + produit_in + "**")

    col2, col3 = st.columns(2)
    with col2:
        quantite_in = st.number_input("الكمية", min_value=1, step=1, key="in_qty")
    with col3:
        type_in = st.selectbox("النوع", types, key="in_type")
    nom_in = st.selectbox("المنزل", manazil, key="in_nom")
    date_in = st.date_input("📅 التاريخ", value=date.today(), key="in_date")
    time_in = st.time_input("🕐 الوقت", value=datetime.now().time(), key="in_time")
    sijil_in = nom_in + " / " + produit_in + "/" + type_in + "/" + str(quantite_in)
    st.info("📝 استلام... " + sijil_in)
    if st.button("✅ تأكيد الاستلام", use_container_width=True):
        tar = format_date_arabic(datetime.combine(date_in, time_in))
        df_ops = get_df_ops()
        naqis = 0
        if not df_ops.empty:
            df_m = df_ops[(df_ops["المنزل"]==nom_in)&(df_ops["المنتج"]==produit_in)&(df_ops["الصنف"]==type_in)]
            naqis = df_m[df_m["النوع"]=="إخراج"]["الكمية"].sum() - df_m[df_m["النوع"]=="استلام"]["الكمية"].sum() - quantite_in
        if save_operation(tar, "استلام", nom_in, produit_in, type_in, quantite_in, "استلام... " + sijil_in):
            if naqis > 0:
                st.warning("⚠️ تم الاستلام لكن هناك ناقص: " + str(int(naqis)) + " قطعة")
            else:
                st.success("✅ تم الاستلام وحُفظ: " + sijil_in)

# ── البيع
with tab3:
    st.markdown("### 🛒 تسجيل بيع")

    v_search = st.text_input("🔍 اكتب اسم المنتج", key="v_search", placeholder="مثال: Bv1")
    filtered_v = [p for p in produits if v_search.strip().lower() in p.lower()] if v_search.strip() else produits
    if "v_prod_selected" not in st.session_state:
        st.session_state["v_prod_selected"] = produits[0] if produits else ""
    if v_search.strip():
        if filtered_v:
            cols_btn = st.columns(3)
            for i, p in enumerate(filtered_v[:9]):
                with cols_btn[i % 3]:
                    if st.button(p, key="v_btn_" + p, use_container_width=True):
                        st.session_state["v_prod_selected"] = p
                        st.rerun()
        else:
            st.warning("لا يوجد منتج بهذا الاسم")
    produit_v = st.session_state["v_prod_selected"]
    st.info("✅ المنتج المختار: **" + produit_v + "**")

    col1, col2 = st.columns(2)
    with col1:
        quantite_v = st.number_input("الكمية", min_value=1, step=1, key="v_qty")
    with col2:
        type_v = st.selectbox("النوع", types, key="v_type")
    date_v = st.date_input("📅 التاريخ", value=date.today(), key="v_date")
    time_v = st.time_input("🕐 الوقت", value=datetime.now().time(), key="v_time")
    st.info("📝 بيع... " + produit_v + "/" + type_v + "/" + str(quantite_v))
    if st.button("✅ تأكيد البيع", use_container_width=True):
        tar = format_date_arabic(datetime.combine(date_v, time_v))
        if save_vente(tar, produit_v, type_v, quantite_v):
            st.success("✅ تم تسجيل البيع وخرج من المخزون!")

    st.divider()
    st.markdown("#### 📜 سجل المبيعات")
    df_ventes = get_df_ventes()
    if not df_ventes.empty:
        st.dataframe(df_ventes[["التاريخ","المنتج","الصنف","الكمية"]], use_container_width=True)
        st.divider()
        for idx, row in df_ventes.iterrows():
            col_r, col_d = st.columns([5, 1])
            with col_r:
                st.write("**" + str(row["التاريخ"]) + "** | " + str(row["المنتج"]) + " | " + str(row["الصنف"]) + " | " + str(row["الكمية"]))
            with col_d:
                if st.button("🗑️", key="del_v_" + str(idx)):
                    st.session_state["confirm_v_" + str(idx)] = True
            if st.session_state.get("confirm_v_" + str(idx)):
                st.warning("⚠️ راك سور؟")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ تأكيد", key="yes_v_" + str(idx), use_container_width=True):
                        delete_vente(idx)
                        st.session_state["confirm_v_" + str(idx)] = False
                        st.rerun()
                with c2:
                    if st.button("❌ إلغاء", key="no_v_" + str(idx), use_container_width=True):
                        st.session_state["confirm_v_" + str(idx)] = False
                        st.rerun()
    else:
        st.info("لا توجد مبيعات بعد.")

# ── المخزن
with tab4:
    st.markdown("### 🏪 المخزن")
    if st.button("🔄 تحديث المخزن", use_container_width=True):
        load_operations.clear()
        load_ventes.clear()
        st.rerun()

    df_ops = get_df_ops()
    df_ventes = get_df_ventes()

    if not df_ops.empty:
        df_out = df_ops[df_ops["النوع"]=="إخراج"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
        df_out.columns = ["المنزل","المنتج","الصنف","المُخرَج"]
        df_in = df_ops[df_ops["النوع"]=="استلام"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
        df_in.columns = ["المنزل","المنتج","الصنف","المُستلَم"]
        df_balance = df_out.merge(df_in, on=["المنزل","المنتج","الصنف"], how="left")
        df_balance["المُستلَم"] = df_balance["المُستلَم"].fillna(0).astype(int)

        if not df_ventes.empty:
            df_sold = df_ventes.groupby(["المنتج","الصنف"])["الكمية"].sum().reset_index()
            df_sold.columns = ["المنتج","الصنف","المباع"]
            df_balance = df_balance.merge(df_sold, on=["المنتج","الصنف"], how="left")
            df_balance["المباع"] = df_balance["المباع"].fillna(0).astype(int)
        else:
            df_balance["المباع"] = 0

        df_balance["الرصيد المتبقي"] = df_balance["المُستلَم"] - df_balance["المباع"]
        st.dataframe(df_balance, use_container_width=True)
    else:
        st.info("المخزن فارغ.")

    st.divider()

    # ── زر إضافة منزل جديد
    with st.expander("🏠 ➕ إضافة منزل جديد — السلع"):
        new_manzil_name = st.text_input("✏️ اسم المنزل", placeholder="مثال: محمد", key="makhzan_manzil_input")
        if st.button("➕ إضافة المنزل", use_container_width=True, key="makhzan_add_manzil_btn"):
            if not new_manzil_name.strip():
                st.warning("⚠️ أدخل اسم المنزل أولاً.")
            else:
                try:
                    ws_salaa = get_worksheet("السلع")
                    col_a = ws_salaa.col_values(1)
                    existing = [v.strip() for v in col_a if v.strip()]
                    if new_manzil_name.strip() in existing:
                        st.error("❌ الاسم موجود مسبقاً في السلع.")
                    else:
                        next_row = len(col_a) + 1
                        ws_salaa.update_cell(next_row, 1, new_manzil_name.strip())
                        load_منازل.clear()
                        load_sheet_csv.clear()
                        st.success("✅ تمت إضافة المنزل **" + new_manzil_name.strip() + "** في ورقة السلع!")
                        st.rerun()
                except Exception as e:
                    st.error("❌ خطأ: " + str(e))

    # ── زر إضافة منتج جديد
    with st.expander("📦 ➕ إضافة منتج جديد — الكراس"):
        new_ref_name = st.text_input("✏️ مرجع المنتج", placeholder="مثال: Bv11", key="makhzan_ref_input")
        if st.button("➕ إضافة المنتج", use_container_width=True, key="makhzan_add_ref_btn"):
            if not new_ref_name.strip():
                st.warning("⚠️ أدخل مرجع المنتج أولاً.")
            else:
                try:
                    ws_karras = get_worksheet("الكراس")
                    col_a_k = ws_karras.col_values(1)
                    existing_k = [v.strip() for v in col_a_k if v.strip()]
                    if new_ref_name.strip() in existing_k:
                        st.error("❌ المرجع موجود مسبقاً في الكراس.")
                    else:
                        next_row_k = len(col_a_k) + 1
                        ws_karras.update_cell(next_row_k, 1, new_ref_name.strip())
                        load_produits.clear()
                        load_sheet_csv.clear()
                        st.success("✅ تمت إضافة المنتج **" + new_ref_name.strip() + "** في ورقة الكراس!")
                        st.rerun()
                except Exception as e:
                    st.error("❌ خطأ: " + str(e))

# ── الأخطاء
with tab5:
    st.markdown("### ❌ سجل الأخطاء (الناقص فقط)")
    df_ops = get_df_ops()
    if not df_ops.empty:
        rows = []
        for manzil in df_ops["المنزل"].unique():
            for montaj in df_ops[df_ops["المنزل"]==manzil]["المنتج"].unique():
                for sinf in df_ops[(df_ops["المنزل"]==manzil)&(df_ops["المنتج"]==montaj)]["الصنف"].unique():
                    df_f = df_ops[(df_ops["المنزل"]==manzil)&(df_ops["المنتج"]==montaj)&(df_ops["الصنف"]==sinf)]
                    kh = df_f[df_f["النوع"]=="إخراج"]["الكمية"].sum()
                    s = df_f[df_f["النوع"]=="استلام"]["الكمية"].sum()
                    n = max(0, kh - s)
                    if n > 0:
                        rows.append({"المنزل":manzil,"المنتج":montaj,"الصنف":sinf,"المُخرَج":int(kh),"المُستلَم":int(s),"الناقص":int(n)})
        if rows:
            df_err = pd.DataFrame(rows)
            st.dataframe(df_err, use_container_width=True)
            csv_err = df_err.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ تحميل CSV", csv_err, "alakhtaa.csv", "text/csv")
        else:
            st.success("✅ لا توجد أخطاء!")
    else:
        st.success("✅ لا توجد أخطاء حتى الآن!")

# ── No Livraison
with tab6:
    st.markdown("### 📦 No Livraison")
    col1, col2 = st.columns(2)
    with col1:
        liv_prod = st.selectbox("المنتج", produits, key="liv_prod")
    with col2:
        liv_qty = st.number_input("الكمية المطلوبة", min_value=1, step=1, key="liv_qty")
    if st.button("➕ إضافة الطلبية", use_container_width=True):
        if save_livraison(liv_prod, liv_qty):
            st.success("✅ تمت إضافة طلبية " + liv_prod + " / " + str(liv_qty))
            st.rerun()
    st.divider()
    livs = load_livraisons()
    if livs:
        for liv in livs:
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            with col1:
                st.write("**" + liv["المنتج"] + "**")
            with col2:
                st.write("مطلوب: " + str(liv["الكمية المطلوبة"]))
            with col3:
                st.write("إنتاج: " + str(liv["في الإنتاج"]))
            with col4:
                row_id = liv["row_idx"]
                btn_key = "cancel_" + str(row_id)
                if st.button("🗑️", key=btn_key):
                    cancel_livraison(row_id)
                    st.rerun()
    else:
        st.info("لا توجد طلبيات منتظرة.")

# ── الصور
with tab7:
    st.markdown("### 🖼️ معرض الصور")
    search_ref = st.text_input("🔍 بحث بالمرجع", key="search_img")
    if st.button("🔄 تحديث الصور", use_container_width=True):
        load_images.clear()
        load_sheet_csv.clear()
        st.rerun()
    df_images = load_images()
    if search_ref:
        df_images = df_images[df_images["المرجع"].str.contains(search_ref, case=False, na=False)]
    if df_images.empty:
        st.info("لا توجد صور.")
    else:
        cols = st.columns(3)
        for idx, row in df_images.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                try:
                    st.image(BASE_IMAGE_URL + str(row["الرابط"]).strip(), caption=str(row["المرجع"]).strip(), use_column_width=True)
                except Exception:
                    st.error("❌ " + str(row["المرجع"]))

# ── History
with tab8:
    st.markdown("### 📊 History — كل السجلات")
    if st.button("🔄 تحديث", use_container_width=True, key="ref_hist"):
        load_operations.clear()
        st.rerun()

    df_ops = get_df_ops()
    if not df_ops.empty:
        st.markdown("#### 📈 ملخص")
        df_sum = df_ops.groupby(["المنزل","المنتج","الصنف","النوع"])["الكمية"].sum().unstack(fill_value=0).reset_index()
        st.dataframe(df_sum, use_container_width=True)
        st.divider()
        st.markdown("#### 📜 التفاصيل مع البحث والحذف")
        show_records_with_delete(df_ops, "hist", delete_operation, manazil, produits)
    else:
        st.info("لا توجد سجلات بعد.")

# ── الملاحظات
with tab9:
    st.markdown("### 📝 الملاحظات")

    with st.expander("➕ إضافة ملاحظة جديدة", expanded=True):
        note_prod = st.selectbox("المنتج", ["— بدون منتج —"] + produits, key="note_prod")
        note_text = st.text_area("✏️ الملاحظة", placeholder="اكتب ملاحظتك هنا...", key="note_text", height=100)

        st.markdown("📷 **الصورة** (اختياري)")
        img_source = st.radio("مصدر الصورة:", ["📁 رفع صورة", "📸 كاميرا"], horizontal=True, key="img_source")

        img_b64 = ""
        img_name = ""

        if img_source == "📁 رفع صورة":
            uploaded = st.file_uploader("اختر صورة", type=["jpg","jpeg","png","webp"], key="note_upload")
            if uploaded:
                img_bytes = uploaded.read()
                # ── ضغط الصورة قبل التحويل لـ base64
                img_b64 = compress_image_to_b64(img_bytes)
                img_name = uploaded.name
                if img_b64:
                    st.image(BytesIO(base64.b64decode(img_b64)), caption=img_name, use_column_width=True)
                    chars = len(img_b64)
                    st.caption("📦 حجم الصورة بعد الضغط: " + str(chars) + " حرف " + ("✅" if chars < 40000 else "⚠️ كبيرة جداً"))
        else:
            camera_img = st.camera_input("📸 التقط صورة", key="note_camera")
            if camera_img:
                img_bytes = camera_img.read()
                # ── ضغط الصورة قبل التحويل لـ base64
                img_b64 = compress_image_to_b64(img_bytes)
                img_name = "camera_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                if img_b64:
                    st.image(BytesIO(base64.b64decode(img_b64)), caption="الصورة الملتقطة", use_column_width=True)
                    chars = len(img_b64)
                    st.caption("📦 حجم الصورة بعد الضغط: " + str(chars) + " حرف " + ("✅" if chars < 40000 else "⚠️ كبيرة جداً"))

        note_date = st.date_input("📅 التاريخ", value=date.today(), key="note_date")
        note_time = st.time_input("🕐 الوقت", value=datetime.now().time(), key="note_time")

        # ── تسجيل صوتي
        st.markdown("🎙️ **ملاحظة صوتية** (اختياري)")
        audio_b64 = ""
        try:
            audio_input = st.audio_input("🎤 اضغط للتسجيل", key="note_audio")
            if audio_input:
                audio_bytes = audio_input.read()
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                st.audio(audio_bytes, format="audio/wav")
                chars = len(audio_b64)
                st.caption("🎵 حجم الصوت: " + str(chars) + " حرف " + ("✅" if chars < 40000 else "⚠️ كبير جداً - لن يُحفظ"))
        except Exception:
            st.info("ℹ️ التسجيل الصوتي غير متاح في هذا الإصدار.")
            audio_b64 = ""

        if st.button("💾 حفظ الملاحظة", use_container_width=True):
            if not note_text.strip() and not img_b64 and not audio_b64:
                st.warning("⚠️ أدخل ملاحظة أو أضف صورة أو سجّل صوتاً على الأقل.")
            else:
                dt = datetime.combine(note_date, note_time)
                tar = format_date_arabic(dt)
                montaj_note = "" if note_prod == "— بدون منتج —" else note_prod
                if save_note(tar, montaj_note, note_text.strip(), img_b64, img_name, audio_b64):
                    st.success("✅ تم حفظ الملاحظة!")
                    st.rerun()

    st.divider()
    st.markdown("#### 📋 سجل الملاحظات")
    if st.button("🔄 تحديث الملاحظات", use_container_width=True, key="ref_notes"):
        load_notes.clear()
        st.rerun()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_prod = st.text_input("🔍 بحث بالمنتج", key="f_note_prod")
    with col_f2:
        f_date = st.text_input("📅 بحث بالتاريخ", placeholder="2026-05-21", key="f_note_date")

    df_notes = load_notes()

    if not df_notes.empty:
        df_nd = df_notes.copy()
        if f_prod:
            df_nd = df_nd[df_nd["المنتج"].str.contains(f_prod, na=False, case=False)]
        if f_date:
            df_nd = df_nd[df_nd["التاريخ"].str.contains(f_date, na=False)]

        if df_nd.empty:
            st.info("لا توجد نتائج.")
        else:
            df_nd = df_nd.iloc[::-1].reset_index()
            orig_indices = df_nd["index"].tolist()
            df_nd = df_nd.drop(columns=["index"])

            for i, (_, row) in enumerate(df_nd.iterrows()):
                orig_idx = orig_indices[i]
                st.markdown("---")
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    prod_label = (" | 🏷️ " + str(row["المنتج"])) if row.get("المنتج") else ""
                    st.markdown("🕐 **" + str(row["التاريخ"]) + "**" + prod_label)
                with col_del:
                    if st.button("🗑️", key="del_note_" + str(orig_idx)):
                        st.session_state["confirm_note_" + str(orig_idx)] = True

                if row.get("الملاحظة"):
                    st.write("📝 " + str(row["الملاحظة"]))

                if row.get("الصورة_base64") and str(row["الصورة_base64"]).strip():
                    try:
                        img_data = base64.b64decode(str(row["الصورة_base64"]))
                        img_label = str(row.get("اسم_الصورة", "صورة")) or "صورة"
                        st.image(img_data, caption=img_label, use_column_width=True)
                    except Exception:
                        st.warning("⚠️ تعذر عرض الصورة.")

                if row.get("الصوت_base64") and str(row["الصوت_base64"]).strip():
                    try:
                        audio_data = base64.b64decode(str(row["الصوت_base64"]))
                        st.audio(audio_data, format="audio/wav")
                    except Exception:
                        st.warning("⚠️ تعذر تشغيل الصوت.")

                conf_key = "confirm_note_" + str(orig_idx)
                if st.session_state.get(conf_key):
                    st.warning("⚠️ راك سور؟ متتمنيكش إذا فاصيت متوليش!")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ تأكيد", key="yes_note_" + str(orig_idx), use_container_width=True):
                            delete_note(orig_idx)
                            st.session_state[conf_key] = False
                            st.rerun()
                    with c2:
                        if st.button("❌ إلغاء", key="no_note_" + str(orig_idx), use_container_width=True):
                            st.session_state[conf_key] = False
                            st.rerun()
    else:
        st.info("لا توجد ملاحظات بعد.")
