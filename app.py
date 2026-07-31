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
import time
import threading

# ── Keep-Alive: يمنع Streamlit Cloud من إيقاف التطبيق عند عدم النشاط
def _keep_alive():
    while True:
        time.sleep(240)

_t = threading.Thread(target=_keep_alive, daemon=True)
if not st.session_state.get("_ka_started"):
    _t.start()
    st.session_state["_ka_started"] = True

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

def parse_arabic_date_full(s):
    """يحول نص التاريخ العربي المخزن (مثال: الثلاثاء 02/06/26 14:25) إلى (date, time)
    لاستخدامه كقيم افتراضية عند فتح نموذج التعديل. في حال الفشل يرجع الوقت الحالي."""
    import re
    if isinstance(s, str):
        m = re.search(r'(\d{2})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})', s)
        if m:
            dd, mo, yy, hh, mn = m.groups()
            try:
                dt = datetime.strptime("20" + yy + "-" + mo + "-" + dd + " " + hh + ":" + mn, "%Y-%m-%d %H:%M")
                return dt.date(), dt.time()
            except Exception:
                pass
    return date.today(), datetime.now().time()

def _options_with_current(options_list, current_value):
    """يبني قائمة اختيارات تحتوي القيمة الحالية حتى لو لم تكن موجودة أصلاً في القائمة،
    لتفادي أخطاء selectbox عند تعديل سجل قديم يحوي قيمة غير موجودة حالياً."""
    opts = [o for o in options_list if o is not None]
    current_value = "" if current_value is None else str(current_value)
    if current_value not in opts:
        opts = [current_value] + opts
    return opts

def _arabic_date_sort_key(s):
    """يحوّل نص التاريخ العربي إلى datetime حقيقي للترتيب الزمني الصحيح
    (الترتيب النصي العادي يرتب حسب اسم اليوم أبجدياً وهذا خطأ). أي سجل يتعذر
    تحليله يوضع في آخر الترتيب بدل أن يظهر خطأً في الأعلى."""
    import re
    if isinstance(s, str):
        m = re.search(r'(\d{2})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})', s)
        if m:
            dd, mo, yy, hh, mn = m.groups()
            try:
                return datetime.strptime("20" + yy + "-" + mo + "-" + dd + " " + hh + ":" + mn, "%Y-%m-%d %H:%M")
            except Exception:
                pass
    return datetime.min

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
/* إخفاء زر fullscreen في الجداول لمنع مشكلة عدم الرجوع */
[data-testid="StyledFullScreenButton"] {
    display: none !important;
}
/* إخفاء زر تحميل و بحث داخل الجداول */
[data-testid="stElementToolbar"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── زر رجوع ثابت في أعلى الشاشة
st.markdown("""
<style>
.back-btn-fixed {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 99999;
    background: rgba(255,255,255,0.13);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 10px;
    padding: 7px 16px;
    color: white;
    font-size: 20px;
    cursor: pointer;
    backdrop-filter: blur(6px);
}
</style>
<button class="back-btn-fixed" onclick="window.history.back()">⬅️</button>
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
    for attempt in range(3):
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=SCOPES
            )
            return gspread.authorize(creds).open_by_key(sheet_id)
        except Exception as e:
            if attempt == 2:
                st.error("❌ تعذّر الاتصال بـ Google Sheets. تحقق من الإنترنت.")
                raise e
            time.sleep(3)

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

@st.cache_data(ttl=180)
def load_sheet_csv(name):
    url = "https://docs.google.com/spreadsheets/d/" + sheet_id + "/gviz/tq?tqx=out:csv&sheet=" + quote(name)
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return pd.read_csv(StringIO(r.text))
        except Exception as e:
            if attempt == 2:
                st.warning("⚠️ تعذّر تحميل البيانات (" + name + "). تحقق من الاتصال.")
                return pd.DataFrame()
            time.sleep(2 * (attempt + 1))

@st.cache_data(ttl=300)
def load_produits():
    df = load_sheet_csv("الكراس")
    return df["Référence"].dropna().tolist()

@st.cache_data(ttl=300)
def load_types():
    df = load_sheet_csv("الكراس")
    return [c.strip() for c in df.columns[1:] if c.strip()] or ["FN", "CT"]

@st.cache_data(ttl=300)
def load_منازل():
    df = load_sheet_csv("السلع")
    col = df.iloc[:, 0].dropna()
    return col[col.str.strip() != ""].tolist()

@st.cache_data(ttl=120)
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

def edit_operation(row_idx, tar, naw, manzil, montaj, sinf, kamia):
    """يعدّل سجلاً موجوداً في History (صف row_idx بالترتيب 0-index) بالقيم الجديدة."""
    try:
        ws = get_worksheet("History")
        kamia = int(kamia)
        sajil = naw + "... " + manzil + " / " + montaj + "/" + sinf + "/" + str(kamia)
        ws.update(range_name="A" + str(row_idx + 2) + ":G" + str(row_idx + 2),
                  values=[[tar, naw, manzil, montaj, sinf, kamia, sajil]])
        load_operations.clear()
        return True
    except Exception as e:
        st.warning("خطأ في التعديل: " + str(e))
        return False

@st.cache_data(ttl=120)
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

def edit_vente(row_idx, tar, montaj, sinf, kamia):
    """يعدّل سجل بيع موجود (صف row_idx بالترتيب 0-index) بالقيم الجديدة."""
    try:
        ws = get_worksheet("البيع")
        kamia = int(kamia)
        sajil = "بيع... " + montaj + "/" + sinf + "/" + str(kamia)
        ws.update(range_name="A" + str(row_idx + 2) + ":G" + str(row_idx + 2),
                  values=[[tar, "بيع", "", montaj, sinf, kamia, sajil]])
        load_ventes.clear()
        return True
    except Exception as e:
        st.warning("خطأ في التعديل: " + str(e))
        return False

@st.cache_data(ttl=120)
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

@st.cache_data(ttl=300)
def load_images():
    try:
        df = load_sheet_csv("الصور")
        df.columns = ["الرابط", "المرجع"] + list(df.columns[2:])
        df = df[["المرجع", "الرابط"]].dropna(subset=["المرجع", "الرابط"])
        return df[(df["المرجع"].str.strip() != "") & (df["الرابط"].str.strip() != "")]
    except Exception:
        return pd.DataFrame(columns=["المرجع", "الرابط"])

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

def show_records_with_delete(df, tab_key, delete_fn, manazil_list, produits_list, edit_fn=None, types_list=None):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        s_manzil = st.text_input("🔍 بحث بالمنزل", key="s_manzil_" + tab_key)
    with col_s2:
        s_montaj = st.text_input("🔍 بحث بالمنتج", key="s_montaj_" + tab_key)

    col_s3, col_s4 = st.columns(2)
    with col_s3:
        # ── بحث بالتاريخ عبر date_input مع دعم الفاصل الزمني
        use_date = st.checkbox("📅 تفعيل فلتر التاريخ", key="use_date_" + tab_key)
        if use_date:
            s_date_from = st.date_input("📅 من", value=date.today(), key="s_date_from_" + tab_key)
            use_date_to = st.checkbox("📅 إلى (فاصل زمني)", key="use_date_to_" + tab_key)
            if use_date_to:
                s_date_to = st.date_input("📅 إلى", value=date.today(), key="s_date_to_" + tab_key)
            else:
                s_date_to = None
        else:
            s_date_from = None
            s_date_to = None
    with col_s4:
        if "الصنف" in df.columns:
            available_types = sorted(df["الصنف"].dropna().unique().tolist())
        else:
            available_types = []
        fixed_types = ["FN", "CT", "NTG", "BT"]
        all_types = ["الكل"] + sorted(set(fixed_types + available_types))
        s_sinf = st.selectbox("📂 فلتر الصنف", all_types, key="s_sinf_" + tab_key)

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
    if s_date_from is not None:
        if s_date_to is not None:
            import re as _re
            def in_range(tar_str):
                try:
                    m = _re.search(r'(\d{2})/(\d{2})/(\d{2})', str(tar_str))
                    if m:
                        d_val = datetime.strptime(m.group(0), "%d/%m/%y").date()
                        return s_date_from <= d_val <= s_date_to
                except Exception:
                    pass
                return False
            df_f = df_f[df_f["التاريخ"].apply(in_range)]
        else:
            s_tar = s_date_from.strftime("%d/%m/%y")
            df_f = df_f[df_f["التاريخ"].str.contains(s_tar, na=False)]
    if s_sinf and s_sinf != "الكل":
        df_f = df_f[df_f["الصنف"].str.strip().str.upper() == s_sinf.upper()]

    if df_f.empty:
        st.info("لا توجد نتائج.")
        return

    # ── ترتيب زمني صحيح (الأحدث أولاً) ليطابق ترتيب جدول الملخص بالأعلى
    df_f = df_f.copy()
    df_f["_sort_dt"] = df_f["التاريخ"].apply(_arabic_date_sort_key)
    df_f = df_f.sort_values("_sort_dt", ascending=False).drop(columns=["_sort_dt"])

    # ── تحديد عدد النتائج المعروضة لتخفيف الحمل (كل سجل يعرض أزرار تفاعلية)
    total_matches = len(df_f)
    MAX_SHOWN = 30
    if total_matches > MAX_SHOWN:
        st.caption(f"🔎 تُعرض أحدث {MAX_SHOWN} نتيجة من أصل {total_matches} — ضيّق البحث لعرض نتائج أدق.")
        df_f = df_f.head(MAX_SHOWN)

    _types_opts = types_list or ["FN", "CT", "NTG", "BT"]

    for idx, row in df_f.iterrows():
        if edit_fn is not None:
            col_r, col_e, col_d = st.columns([4, 1, 1])
        else:
            col_r, col_d = st.columns([5, 1])
        with col_r:
            st.write("**" + str(row["التاريخ"]) + "** | " + str(row.get("النوع","")) + " | " + str(row["المنزل"]) + " | " + str(row["المنتج"]) + " | " + str(row["الصنف"]) + " | " + str(row["الكمية"]))
        if edit_fn is not None:
            with col_e:
                edit_key = "edit_" + tab_key + "_" + str(idx)
                if st.button("✏️", key=edit_key):
                    st.session_state["show_edit_" + tab_key + "_" + str(idx)] = not st.session_state.get("show_edit_" + tab_key + "_" + str(idx), False)
        with col_d:
            del_key = "del_" + tab_key + "_" + str(idx)
            if st.button("🗑️", key=del_key):
                st.session_state["confirm_" + tab_key + "_" + str(idx)] = True

        # ── نموذج التعديل (يظهر عند الضغط على ✏️)
        if edit_fn is not None and st.session_state.get("show_edit_" + tab_key + "_" + str(idx)):
            with st.container(border=True):
                st.markdown("##### ✏️ تعديل السجل")
                def_date, def_time = parse_arabic_date_full(str(row["التاريخ"]))
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_date = st.date_input("📅 التاريخ", value=def_date, key="e_date_" + tab_key + "_" + str(idx))
                with ec2:
                    e_time = st.time_input("🕐 الوقت", value=def_time, key="e_time_" + tab_key + "_" + str(idx))

                naw_opts = ["إخراج", "استلام"]
                cur_naw = str(row.get("النوع", "")) or naw_opts[0]
                naw_opts_full = _options_with_current(naw_opts, cur_naw)
                e_naw = st.selectbox("النوع", naw_opts_full, index=naw_opts_full.index(cur_naw), key="e_naw_" + tab_key + "_" + str(idx))

                manzil_opts = _options_with_current(manazil_list, row["المنزل"])
                e_manzil = st.selectbox("المنزل", manzil_opts, index=manzil_opts.index(str(row["المنزل"])), key="e_manzil_" + tab_key + "_" + str(idx))

                montaj_opts = _options_with_current(produits_list, row["المنتج"])
                e_montaj = st.selectbox("المنتج", montaj_opts, index=montaj_opts.index(str(row["المنتج"])), key="e_montaj_" + tab_key + "_" + str(idx))

                ec3, ec4 = st.columns(2)
                with ec3:
                    sinf_opts = _options_with_current(_types_opts, row["الصنف"])
                    e_sinf = st.selectbox("الصنف", sinf_opts, index=sinf_opts.index(str(row["الصنف"])), key="e_sinf_" + tab_key + "_" + str(idx))
                with ec4:
                    try:
                        def_kamia = int(row["الكمية"])
                    except Exception:
                        def_kamia = 1
                    e_kamia = st.number_input("الكمية", min_value=1, step=1, value=max(1, def_kamia), key="e_kamia_" + tab_key + "_" + str(idx))

                ec5, ec6 = st.columns(2)
                with ec5:
                    if st.button("💾 حفظ التعديل", key="save_edit_" + tab_key + "_" + str(idx), use_container_width=True):
                        e_tar = format_date_arabic(datetime.combine(e_date, e_time))
                        if edit_fn(idx, e_tar, e_naw, e_manzil, e_montaj, e_sinf, e_kamia):
                            st.success("✅ تم تعديل السجل بنجاح!")
                            st.session_state["show_edit_" + tab_key + "_" + str(idx)] = False
                            st.rerun()
                with ec6:
                    if st.button("❌ إلغاء", key="cancel_edit_" + tab_key + "_" + str(idx), use_container_width=True):
                        st.session_state["show_edit_" + tab_key + "_" + str(idx)] = False
                        st.rerun()

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
    for fn in [load_produits, load_types, load_منازل, load_operations, load_ventes, load_livraisons, load_images, load_sheet_csv]:
        fn.clear()
    st.rerun()

TAB_NAMES = [
    "📤 إخراج", "📥 استلام", "🛒 البيع", "🏪 المخزن", "❌ الأخطاء",
    "📦 No Livraison", "🖼️ الصور", "📊 History"
]

# ── شريط تنقّل يدوي بديل عن st.tabs
# ملاحظة أداء مهمة: st.tabs في Streamlit تُنفّذ كود كل التبويبات في كل مرة
# (حتى غير الظاهرة)، وهذا كان سبب رئيسي للبطء. مع هذا الأسلوب (radio + if/elif)
# يُنفَّذ فقط كود القسم المختار فعلياً، والباقي لا يشتغل إطلاقاً حتى تفتحه.
st.markdown("""
<style>
div[role="radiogroup"] {
    flex-wrap: wrap;
    gap: 6px;
}
div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
    padding: 6px 12px;
    margin: 0 !important;
}
div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(224,176,96,0.25);
    border: 1px solid #e0b060;
}
</style>
""", unsafe_allow_html=True)

if "active_section" not in st.session_state:
    st.session_state["active_section"] = TAB_NAMES[0]

selected_tab = st.radio(
    "الأقسام", TAB_NAMES,
    horizontal=True,
    key="active_section",
    label_visibility="collapsed"
)

# ── إخراج
if selected_tab == TAB_NAMES[0]:
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
elif selected_tab == TAB_NAMES[1]:
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
elif selected_tab == TAB_NAMES[2]:
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
        df_ventes_sorted = df_ventes.copy()
        df_ventes_sorted["_sort_dt"] = df_ventes_sorted["التاريخ"].apply(_arabic_date_sort_key)
        df_ventes_sorted = df_ventes_sorted.sort_values("_sort_dt", ascending=False).drop(columns=["_sort_dt"])
        total_ventes = len(df_ventes_sorted)
        MAX_VENTES_SHOWN = 30
        if total_ventes > MAX_VENTES_SHOWN:
            st.caption(f"🔎 تُعرض أحدث {MAX_VENTES_SHOWN} عملية بيع من أصل {total_ventes} (الجدول أعلاه يعرضها كلها).")
            df_ventes_sorted = df_ventes_sorted.head(MAX_VENTES_SHOWN)
        for idx, row in df_ventes_sorted.iterrows():
            col_r, col_e, col_d = st.columns([4, 1, 1])
            with col_r:
                st.write("**" + str(row["التاريخ"]) + "** | " + str(row["المنتج"]) + " | " + str(row["الصنف"]) + " | " + str(row["الكمية"]))
            with col_e:
                if st.button("✏️", key="edit_v_" + str(idx)):
                    st.session_state["show_edit_v_" + str(idx)] = not st.session_state.get("show_edit_v_" + str(idx), False)
            with col_d:
                if st.button("🗑️", key="del_v_" + str(idx)):
                    st.session_state["confirm_v_" + str(idx)] = True

            if st.session_state.get("show_edit_v_" + str(idx)):
                with st.container(border=True):
                    st.markdown("##### ✏️ تعديل البيع")
                    def_date_v, def_time_v = parse_arabic_date_full(str(row["التاريخ"]))
                    evc1, evc2 = st.columns(2)
                    with evc1:
                        ev_date = st.date_input("📅 التاريخ", value=def_date_v, key="ev_date_" + str(idx))
                    with evc2:
                        ev_time = st.time_input("🕐 الوقت", value=def_time_v, key="ev_time_" + str(idx))

                    ev_montaj_opts = _options_with_current(produits, row["المنتج"])
                    ev_montaj = st.selectbox("المنتج", ev_montaj_opts, index=ev_montaj_opts.index(str(row["المنتج"])), key="ev_montaj_" + str(idx))

                    evc3, evc4 = st.columns(2)
                    with evc3:
                        ev_sinf_opts = _options_with_current(types, row["الصنف"])
                        ev_sinf = st.selectbox("الصنف", ev_sinf_opts, index=ev_sinf_opts.index(str(row["الصنف"])), key="ev_sinf_" + str(idx))
                    with evc4:
                        try:
                            def_kamia_v = int(row["الكمية"])
                        except Exception:
                            def_kamia_v = 1
                        ev_kamia = st.number_input("الكمية", min_value=1, step=1, value=max(1, def_kamia_v), key="ev_kamia_" + str(idx))

                    evc5, evc6 = st.columns(2)
                    with evc5:
                        if st.button("💾 حفظ التعديل", key="save_edit_v_" + str(idx), use_container_width=True):
                            ev_tar = format_date_arabic(datetime.combine(ev_date, ev_time))
                            if edit_vente(idx, ev_tar, ev_montaj, ev_sinf, ev_kamia):
                                st.success("✅ تم تعديل البيع بنجاح!")
                                st.session_state["show_edit_v_" + str(idx)] = False
                                st.rerun()
                    with evc6:
                        if st.button("❌ إلغاء", key="cancel_edit_v_" + str(idx), use_container_width=True):
                            st.session_state["show_edit_v_" + str(idx)] = False
                            st.rerun()

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
elif selected_tab == TAB_NAMES[3]:
    st.markdown("### 🏪 المخزن")
    if st.button("🔄 تحديث المخزن", use_container_width=True):
        load_operations.clear()
        load_ventes.clear()
        st.rerun()

    df_ops = get_df_ops()
    df_ventes = get_df_ventes()

    if not df_ops.empty:
        # ── فلاتر
        mk_col1, mk_col2 = st.columns(2)
        with mk_col1:
            mk_sinf_opts = ["الكل"] + sorted(set(["FN","CT","NTG","BT"] + df_ops["الصنف"].dropna().unique().tolist()))
            mk_sinf = st.selectbox("📂 فلتر الصنف", mk_sinf_opts, key="mk_sinf")
        with mk_col2:
            mk_manzil_search = st.text_input("🔍 بحث بالمنزل", key="mk_manzil_search")

        mk_col3, mk_col4 = st.columns(2)
        with mk_col3:
            mk_montaj_search = st.text_input("🔍 بحث بالمنتج", key="mk_montaj_search")
        with mk_col4:
            mk_use_date = st.checkbox("📅 فلتر بالتاريخ", key="mk_use_date")
            if mk_use_date:
                mk_date = st.date_input("اختر التاريخ", value=date.today(), key="mk_date")
                mk_date_str = mk_date.strftime("%d/%m/%y")
            else:
                mk_date_str = ""

        # ── تطبيق الفلاتر على البيانات الخام (مع الاحتفاظ بالتاريخ)
        df_ops_f = df_ops.copy()
        if mk_sinf != "الكل":
            df_ops_f = df_ops_f[df_ops_f["الصنف"].str.strip().str.upper() == mk_sinf.upper()]
        if mk_date_str:
            df_ops_f = df_ops_f[df_ops_f["التاريخ"].str.contains(mk_date_str, na=False)]
        if mk_manzil_search.strip():
            df_ops_f = df_ops_f[df_ops_f["المنزل"].str.contains(mk_manzil_search.strip(), case=False, na=False)]
        if mk_montaj_search.strip():
            df_ops_f = df_ops_f[df_ops_f["المنتج"].str.contains(mk_montaj_search.strip(), case=False, na=False)]

        if df_ops_f.empty:
            st.info("لا توجد نتائج.")
        else:
            # ── جدول يحتوي على التاريخ مع ملخص الكميات
            df_out = df_ops_f[df_ops_f["النوع"]=="إخراج"].groupby(["التاريخ","المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
            df_out.columns = ["التاريخ","المنزل","المنتج","الصنف","المُخرَج"]
            df_in  = df_ops_f[df_ops_f["النوع"]=="استلام"].groupby(["التاريخ","المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
            df_in.columns  = ["التاريخ","المنزل","المنتج","الصنف","المُستلَم"]

            if not df_out.empty and not df_in.empty:
                df_balance = df_out.merge(df_in, on=["التاريخ","المنزل","المنتج","الصنف"], how="outer").fillna(0)
            elif df_out.empty:
                df_balance = df_in.copy(); df_balance["المُخرَج"] = 0
            else:
                df_balance = df_out.copy(); df_balance["المُستلَم"] = 0

            df_balance["المُخرَج"]  = df_balance["المُخرَج"].astype(int)
            df_balance["المُستلَم"] = df_balance["المُستلَم"].astype(int)

            if not df_ventes.empty:
                df_sold = df_ventes.groupby(["المنتج","الصنف"])["الكمية"].sum().reset_index()
                df_sold.columns = ["المنتج","الصنف","المباع"]
                df_balance = df_balance.merge(df_sold, on=["المنتج","الصنف"], how="left")
                df_balance["المباع"] = df_balance["المباع"].fillna(0).astype(int)
            else:
                df_balance["المباع"] = 0

            df_balance["الرصيد"] = df_balance["المُستلَم"] - df_balance["المباع"]

            # ── عرض الجدول كـ HTML مع التاريخ وبدون fullscreen مشكلة
            cols_order = ["التاريخ","المنزل","المنتج","الصنف","المُخرَج","المُستلَم","المباع","الرصيد"]
            cols_order = [c for c in cols_order if c in df_balance.columns]
            df_show = df_balance[cols_order].sort_values("التاريخ", ascending=False).reset_index(drop=True)

            # بناء HTML جدول
            rows_html = ""
            for _, r in df_show.iterrows():
                rows_html += "<tr>" + "".join(f"<td style='padding:6px 10px;border-bottom:1px solid #333;text-align:center'>{v}</td>" for v in r) + "</tr>"
            headers_html = "".join(f"<th style='padding:8px 10px;background:#1a1a2e;color:#e0b060;text-align:center'>{c}</th>" for c in df_show.columns)
            table_html = f"""
<div style='overflow-x:auto;border-radius:10px;border:1px solid #333'>
<table style='width:100%;border-collapse:collapse;color:white;font-size:13px'>
<thead><tr>{headers_html}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""
            st.markdown(table_html, unsafe_allow_html=True)
            st.caption(f"📊 إجمالي السجلات: {len(df_show)}")
    else:
        st.info("المخزن فارغ.")

    st.divider()

    # ── تعديل / حذف المعاملات الأصلية المسجّلة (إخراج/استلام) — ابحث بالمنزل ثم اضغط ✏️
    st.markdown("#### ✏️ تعديل أو حذف معاملة مسجّلة سابقاً")
    st.caption("ابحث بالمنزل أو المنتج، ثم اضغط ✏️ بجانب السجل المطلوب لعرض معلوماته وتعديلها.")
    if not df_ops.empty:
        show_records_with_delete(df_ops, "makhzan", delete_operation, manazil, produits, edit_fn=edit_operation, types_list=types)
    else:
        st.info("لا توجد معاملات مسجّلة بعد.")

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
elif selected_tab == TAB_NAMES[4]:
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
elif selected_tab == TAB_NAMES[5]:
    st.markdown("### 📦 No Livraison")

    # ── قسم إضافة طلبية (مصغّر في expander)
    with st.expander("➕ إضافة طلبية جديدة"):
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

    # ── جدول: كل المنازل + آخر عملية لكل منزل من History
    st.markdown("#### 🏠 آخر عمل لكل منزل")

    df_ops_liv = get_df_ops()

    # دالة لتحويل التاريخ العربي إلى datetime للترتيب
    def parse_arabic_date_py(s):
        if not isinstance(s, str):
            return None
        import re
        m = re.search(r'(\d{2})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})', s)
        if m:
            dd, mo, yy, hh, mn = m.groups()
            try:
                return datetime.strptime(f"20{yy}-{mo}-{dd} {hh}:{mn}", "%Y-%m-%d %H:%M")
            except Exception:
                return None
        return None

    # ── فلتر الصنف + اختيار الجيل
    col_liv_filter, col_liv_gen = st.columns([3, 1])
    with col_liv_filter:
        fixed_types_liv = ["BT", "CT", "FN", "NTG"]
        if not df_ops_liv.empty and "الصنف" in df_ops_liv.columns:
            extra_types = sorted(df_ops_liv["الصنف"].dropna().unique().tolist())
            all_types_liv = ["الكل"] + sorted(set(fixed_types_liv + extra_types))
        else:
            all_types_liv = ["الكل"] + fixed_types_liv
        liv_sinf_filter = st.selectbox("🗂️ فلتر الصنف", all_types_liv, key="liv_sinf_filter")
    with col_liv_gen:
        liv_generation = st.number_input(
            "🔢 الجيل",
            min_value=1,
            step=1,
            value=1,
            key="liv_generation",
            help="1 = آخر عمل، 2 = قبل الأخير، 3 = ما قبله، وهكذا..."
        )

    if liv_generation > 1:
        gen_label = {2: "قبل الأخير", 3: "ما قبل قبل الأخير"}.get(liv_generation, f"الجيل {liv_generation}")
        st.info(f"⏳ تعرض الجيل **{int(liv_generation)}** — {gen_label} لكل منزل")

    if not df_ops_liv.empty and "المنزل" in df_ops_liv.columns:
        # فلتر: فقط السجلات التي فيها منزل
        df_with_manzil = df_ops_liv[df_ops_liv["المنزل"].str.strip() != ""].copy()

        # تطبيق فلتر الصنف قبل استخراج العمليات
        if liv_sinf_filter != "الكل":
            df_with_manzil = df_with_manzil[df_with_manzil["الصنف"].str.strip().str.upper() == liv_sinf_filter.upper()]

        if not df_with_manzil.empty:
            # تحويل التاريخ للترتيب
            df_with_manzil["_sort_date"] = df_with_manzil["التاريخ"].apply(parse_arabic_date_py)

            # ترتيب تنازلي ثم اختيار الجيل المطلوب لكل منزل
            df_sorted = df_with_manzil.sort_values("_sort_date", ascending=False, na_position="last")

            # استخراج الجيل المطلوب (nth) لكل منزل
            gen_n = int(liv_generation)
            df_last = (
                df_sorted
                .groupby("المنزل", sort=False)
                .nth(gen_n - 1)  # 0-indexed: nth(0)=آخر، nth(1)=قبل الأخير...
                .reset_index()
            )

            # إزالة المنازل التي ليس لديها سجل بالجيل المطلوب (nth تعيد NaN)
            df_last = df_last.dropna(subset=["_sort_date"])

            # ترتيب حسب التاريخ من الأحدث للأقدم
            df_last = df_last.sort_values("_sort_date", ascending=False, na_position="last").reset_index(drop=True)

            # المنازل التي لديها سجلات لكن ليس بالجيل المطلوب
            all_manazil_in_history = set(df_with_manzil["المنزل"].str.strip().tolist())
            manazil_with_gen = set(df_last["المنزل"].str.strip().tolist()) if not df_last.empty else set()
            manazil_without_gen = [m for m in all_manazil_in_history if m.strip() not in manazil_with_gen]

            if not df_last.empty:
                # عرض الجدول
                cols_show = ["المنزل", "التاريخ", "النوع", "المنتج", "الصنف", "الكمية"]
                cols_show = [c for c in cols_show if c in df_last.columns]
                df_display = df_last[cols_show].copy()

                headers_html = "".join(
                    f"<th style='padding:8px 10px;background:#1a1a2e;color:#e0b060;text-align:center'>{c}</th>"
                    for c in df_display.columns
                )
                rows_html = ""
                for _, r in df_display.iterrows():
                    rows_html += "<tr>" + "".join(
                        f"<td style='padding:6px 10px;border-bottom:1px solid #333;text-align:center'>{v}</td>"
                        for v in r
                    ) + "</tr>"

                table_html = f"""
<div style='overflow-x:auto;border-radius:10px;border:1px solid #333'>
<table style='width:100%;border-collapse:collapse;color:white;font-size:13px'>
<thead><tr>{headers_html}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""
                st.markdown(table_html, unsafe_allow_html=True)
                st.caption(f"🏠 إجمالي المنازل: {len(df_last)}")
            else:
                st.info(f"⚠️ لا يوجد منزل لديه جيل رقم {gen_n}.")

            # ── المنازل التي لديها سجلات لكن ليس بالجيل المطلوب (فقط إذا الجيل > 1)
            if gen_n > 1 and manazil_without_gen:
                st.markdown("---")
                st.markdown(f"##### 🏚️ منازل بلا عمل في الجيل {gen_n}:")
                for m in sorted(manazil_without_gen):
                    st.write("• " + m)

            # ── المنازل التي لم تظهر في History أبداً
            manazil_no_history = [m for m in manazil if m.strip() not in all_manazil_in_history]
            if manazil_no_history:
                st.markdown("---")
                st.markdown("##### 🏚️ منازل بلا عمل:")
                for m in manazil_no_history:
                    st.write("• " + m)
        else:
            st.info("لا توجد عمليات مسجّلة للمنازل بعد.")
    else:
        st.info("لا توجد بيانات في History بعد.")

# ── الصور
elif selected_tab == TAB_NAMES[6]:
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
elif selected_tab == TAB_NAMES[7]:
    import streamlit.components.v1 as components
    st.markdown("### 📊 History — كل السجلات")
    if st.button("🔄 تحديث", use_container_width=True, key="ref_hist"):
        load_operations.clear()
        st.rerun()

    df_ops = get_df_ops()
    if not df_ops.empty:
        st.markdown("#### 📈 ملخص")

        # ── فلاتر
        h_col1, h_col2 = st.columns(2)
        with h_col1:
            h_sinf_opts = ["الكل"] + sorted(set(["FN","CT","NTG","BT"] + df_ops["الصنف"].dropna().unique().tolist()))
            h_sinf = st.selectbox("📂 فلتر الصنف", h_sinf_opts, key="h_sinf")
        with h_col2:
            h_use_date = st.checkbox("📅 فلتر بالتاريخ", key="h_use_date")
            if h_use_date:
                h_date_from = st.date_input("📅 من", value=date.today(), key="h_date_from")
                h_use_date_to = st.checkbox("📅 إلى (فاصل زمني)", key="h_use_date_to")
                if h_use_date_to:
                    h_date_to = st.date_input("📅 إلى", value=date.today(), key="h_date_to")
                else:
                    h_date_to = None
            else:
                h_date_from = None
                h_date_to = None

        h_col3, h_col4 = st.columns(2)
        with h_col3:
            h_manzil = st.text_input("🔍 بحث بالمنزل", key="h_manzil")
            if h_manzil:
                sugg = [m for m in manazil if h_manzil.lower() in m.lower()]
                if sugg:
                    chosen = st.selectbox("📌 اختر منزل:", ["—"] + sugg[:6], key="h_manzil_sugg")
                    if chosen != "—":
                        h_manzil = chosen
        with h_col4:
            h_montaj = st.text_input("🔍 بحث بالمنتج", key="h_montaj")
            if h_montaj:
                sugg = [p for p in produits if h_montaj.lower() in p.lower()]
                if sugg:
                    chosen = st.selectbox("📌 اختر منتج:", ["—"] + sugg[:6], key="h_montaj_sugg")
                    if chosen != "—":
                        h_montaj = chosen

        # ── تطبيق الفلاتر
        df_ops_h = df_ops.copy()
        if h_sinf != "الكل":
            df_ops_h = df_ops_h[df_ops_h["الصنف"].str.strip().str.upper() == h_sinf.upper()]
        if h_date_from is not None:
            if h_date_to is not None:
                import re as _re2
                def _in_range_h(tar_str):
                    try:
                        m = _re2.search(r'(\d{2})/(\d{2})/(\d{2})', str(tar_str))
                        if m:
                            from datetime import datetime as _dt
                            d_val = _dt.strptime(m.group(0), "%d/%m/%y").date()
                            return h_date_from <= d_val <= h_date_to
                    except Exception:
                        pass
                    return False
                df_ops_h = df_ops_h[df_ops_h["التاريخ"].apply(_in_range_h)]
            else:
                h_date_str = h_date_from.strftime("%d/%m/%y")
                df_ops_h = df_ops_h[df_ops_h["التاريخ"].str.contains(h_date_str, na=False)]
        if h_manzil and h_manzil != "—":
            df_ops_h = df_ops_h[df_ops_h["المنزل"].str.contains(h_manzil, case=False, na=False)]
        if h_montaj and h_montaj != "—":
            df_ops_h = df_ops_h[df_ops_h["المنتج"].str.contains(h_montaj, case=False, na=False)]

        if df_ops_h.empty:
            st.info("لا توجد نتائج.")
        else:
            df_sum = df_ops_h.groupby(["التاريخ","المنزل","المنتج","الصنف","النوع"])["الكمية"].sum().reset_index()
            df_sum = df_sum.sort_values("التاريخ", ascending=False).reset_index(drop=True)

            # ── تحويل DataFrame لـ JSON لتمريره لـ JavaScript
            import json
            cols = list(df_sum.columns)
            rows_data = df_sum.values.tolist()
            cols_json = json.dumps(cols, ensure_ascii=False)
            rows_json = json.dumps(rows_data, ensure_ascii=False)
            total = len(df_sum)

            # ── component HTML كامل مع ترتيب بالضغط على الرأس
            component_html = f"""<!DOCTYPE html>
<html dir="rtl">
<head>
<meta charset="utf-8">
<style>
  body {{ margin:0; background:#0e0e1a; color:white; font-family:Arial,sans-serif; font-size:13px; }}
  .toolbar {{ padding:8px; background:#0e0e1a; position:sticky; top:0; z-index:10; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
  .btn {{
    background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.25);
    border-radius:8px; padding:7px 16px; color:white; font-size:15px; cursor:pointer;
  }}
  .btn:active {{ background:rgba(255,255,255,0.3); }}
  #back-btn {{ display:none; }}
  .count {{ color:#aaa; font-size:12px; margin-right:8px; }}
  .table-wrap {{ overflow:auto; max-height:360px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{
    background:#1a1a2e; color:#e0b060; padding:8px 10px;
    text-align:center; position:sticky; top:0; white-space:nowrap;
    cursor:pointer; user-select:none;
  }}
  th:hover {{ background:#252545; }}
  th .sort-arrow {{ margin-right:4px; font-size:11px; color:#aaa; }}
  th.asc .sort-arrow::after {{ content:"▲"; color:#e0b060; }}
  th.desc .sort-arrow::after {{ content:"▼"; color:#e0b060; }}
  th:not(.asc):not(.desc) .sort-arrow::after {{ content:"⇅"; color:#666; }}
  td {{ padding:6px 8px; border-bottom:1px solid #2a2a3e; text-align:center; white-space:nowrap; }}
  tr:hover td {{ background:rgba(255,255,255,0.05); }}
  body.fs .table-wrap {{ max-height: calc(100vh - 52px); }}
</style>
</head>
<body>
<div class="toolbar">
  <button class="btn" id="fs-btn" onclick="toggleFS()">⛶ ملء الشاشة</button>
  <button class="btn" id="back-btn" onclick="exitFS()">⬅️ رجوع</button>
  <span class="count" id="count-lbl">📊 {total} سجل</span>
</div>
<div class="table-wrap">
<table id="main-table">
<thead id="thead"></thead>
<tbody id="tbody"></tbody>
</table>
</div>
<script>
var COLS = {cols_json};
var ROWS = {rows_json};
var sortCol = 0;
var sortAsc = false;

function renderTable() {{
  // رأس الجدول
  var thead = document.getElementById('thead');
  var hr = '<tr>';
  COLS.forEach(function(c, i) {{
    var cls = (i===sortCol) ? (sortAsc?'asc':'desc') : '';
    hr += '<th class="'+cls+'" onclick="sortBy('+i+')">' +
          '<span class="sort-arrow"></span>' + c + '</th>';
  }});
  thead.innerHTML = hr + '</tr>';

  // دالة تحويل التاريخ العربي "الثلاثاء 02/06/26 14:25" إلى timestamp للترتيب الصحيح
  function parseArabicDate(s) {{
    s = String(s);
    // استخراج dd/mm/yy HH:MM
    var m = s.match(/(\d{{2}})\/(\d{{2}})\/(\d{{2}})\s+(\d{{2}}):(\d{{2}})/);
    if (m) {{
      var dd=m[1], mo=m[2], yy=m[3], hh=m[4], mn=m[5];
      return new Date('20'+yy+'-'+mo+'-'+dd+'T'+hh+':'+mn+':00').getTime();
    }}
    return null;
  }}

  // ترتيب البيانات
  var sorted = ROWS.slice().sort(function(a,b) {{
    var va = a[sortCol], vb = b[sortCol];
    // أولاً: حاول تفسير كتاريخ عربي
    var da = parseArabicDate(va), db = parseArabicDate(vb);
    if (da !== null && db !== null) {{
      return sortAsc ? da - db : db - da;
    }}
    // ثانياً: حاول مقارنة رقمية
    var na = parseFloat(String(va)), nb = parseFloat(String(vb));
    if (!isNaN(na) && !isNaN(nb)) {{
      return sortAsc ? na - nb : nb - na;
    }}
    // ثالثاً: مقارنة نصية
    va = String(va); vb = String(vb);
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  var tbody = document.getElementById('tbody');
  tbody.innerHTML = sorted.map(function(r) {{
    return '<tr>' + r.map(function(v) {{
      return '<td>'+v+'</td>';
    }}).join('') + '</tr>';
  }}).join('');
}}

function sortBy(i) {{
  if (sortCol === i) {{ sortAsc = !sortAsc; }}
  else {{ sortCol = i; sortAsc = true; }}
  renderTable();
}}

function toggleFS() {{
  var isFS = document.body.classList.toggle('fs');
  document.getElementById('fs-btn').textContent = isFS ? '🗕 تصغير' : '⛶ ملء الشاشة';
  document.getElementById('back-btn').style.display = isFS ? 'inline-block' : 'none';
  if (isFS) {{ if(document.documentElement.requestFullscreen) document.documentElement.requestFullscreen(); }}
  else {{ if(document.exitFullscreen) document.exitFullscreen(); }}
}}
function exitFS() {{
  document.body.classList.remove('fs');
  document.getElementById('fs-btn').textContent = '⛶ ملء الشاشة';
  document.getElementById('back-btn').style.display = 'none';
  if(document.exitFullscreen) document.exitFullscreen();
}}
document.addEventListener('fullscreenchange', function() {{
  if(!document.fullscreenElement) {{
    document.body.classList.remove('fs');
    document.getElementById('fs-btn').textContent = '⛶ ملء الشاشة';
    document.getElementById('back-btn').style.display = 'none';
  }}
}});

// تشغيل أولي
renderTable();
</script>
</body>
</html>"""

            components.html(component_html, height=440, scrolling=False)
            st.caption(f"📊 إجمالي: {total} سجل")

        st.divider()
        st.markdown("#### 📜 التفاصيل مع البحث والتعديل والحذف")
        show_records_with_delete(df_ops, "hist", delete_operation, manazil, produits, edit_fn=edit_operation, types_list=types)
    else:
        st.info("لا توجد سجلات بعد.")

