import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO, BytesIO
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
/* إخفاء لوحة المفاتيح عند selectbox */
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
    except:
        ss = get_spreadsheet()
        ws = ss.add_worksheet(title=name, rows=1000, cols=20)
        ws.append_row(headers)
        return ws

@st.cache_data(ttl=30)
def load_sheet_csv(name):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={quote(name)}"
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

# ── History
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
    except:
        return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

def save_operation(تاريخ, نوع, منزل, منتج, صنف, كمية, سجل):
    try:
        ws = get_worksheet("History")
        if not ws.get_all_values():
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        ws.append_row([تاريخ, نوع, منزل, منتج, صنف, int(كمية), سجل])
        load_operations.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ خطأ في الحفظ: {e}")
        return False

def delete_operation(row_idx):
    try:
        ws = get_worksheet("History")
        ws.delete_rows(row_idx + 2)
        load_operations.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ {e}")
        return False

# ── البيع
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
        st.warning(f"⚠️ خطأ في قراءة البيع: {e}")
        return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

def save_vente(تاريخ, منتج, صنف, كمية):
    try:
        ws = get_worksheet("البيع")
        vals = ws.get_all_values()
        if not vals:
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        سجل = f"بيع... {منتج}/{صنف}/{كمية}"
        ws.append_row([تاريخ, "بيع", "", منتج, صنف, int(كمية), سجل])
        load_ventes.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ خطأ في حفظ البيع: {e}")
        return False

def delete_vente(row_idx):
    try:
        ws = get_worksheet("البيع")
        ws.delete_rows(row_idx + 2)
        load_ventes.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ {e}")
        return False

# ── No Livrai
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
    except:
        return []

def save_livraison(منتج, كمية):
    try:
        ws = get_worksheet("No Livrai")
        if not ws.get_all_values():
            ws.append_row(["المنتج","الكمية المطلوبة","في الإنتاج","الحالة"])
        ws.append_row([منتج, int(كمية), 0, "نشط"])
        load_livraisons.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ {e}")
        return False

def cancel_livraison(row_idx):
    try:
        ws = get_worksheet("No Livrai")
        ws.update_cell(row_idx, 4, "ملغى")
        load_livraisons.clear()
    except Exception as e:
        st.warning(f"⚠️ {e}")

# ── الصور
@st.cache_data(ttl=60)
def load_images():
    try:
        df = load_sheet_csv("الصور")
        df.columns = ["الرابط", "المرجع"] + list(df.columns[2:])
        df = df[["المرجع", "الرابط"]].dropna(subset=["المرجع", "الرابط"])
        return df[(df["المرجع"].str.strip() != "") & (df["الرابط"].str.strip() != "")]
    except:
        return pd.DataFrame(columns=["المرجع", "الرابط"])

# ── الملاحظات
NOTES_SHEET = "الملاحظات"
NOTES_HEADERS = ["التاريخ", "المنتج", "الملاحظة", "الصورة_base64", "اسم_الصورة"]

@st.cache_data(ttl=30)
def load_notes():
    try:
        ws = get_worksheet(NOTES_SHEET)
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame(columns=NOTES_HEADERS)
        df = pd.DataFrame(data[1:], columns=data[0] if data[0] == NOTES_HEADERS else NOTES_HEADERS[:len(data[0])])
        # تأكد من وجود كل الأعمدة
        for col in NOTES_HEADERS:
            if col not in df.columns:
                df[col] = ""
        return df
    except:
        return pd.DataFrame(columns=NOTES_HEADERS)

def save_note(تاريخ, منتج, ملاحظة, img_b64="", img_name=""):
    try:
        ws = get_or_create_worksheet(NOTES_SHEET, NOTES_HEADERS)
        vals = ws.get_all_values()
        if not vals or vals[0] != NOTES_HEADERS:
            ws.insert_row(NOTES_HEADERS, 1)
        ws.append_row([تاريخ, منتج, ملاحظة, img_b64, img_name])
        load_notes.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ خطأ في حفظ الملاحظة: {e}")
        return False

def delete_note(row_idx):
    try:
        ws = get_worksheet(NOTES_SHEET)
        ws.delete_rows(row_idx + 2)
        load_notes.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ {e}")
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

def show_records_with_delete(df, tab_key, delete_fn, منازل_list, produits_list):
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        s_منزل = st.text_input("🔍 بحث بالمنزل", key=f"s_منزل_{tab_key}")
    with col_s2:
        s_منتج = st.text_input("🔍 بحث بالمنتج", key=f"s_منتج_{tab_key}")
    with col_s3:
        s_تاريخ = st.text_input("📅 بحث بالتاريخ", placeholder="2026-05-19", key=f"s_تاريخ_{tab_key}")

    if s_منزل:
        sugg = [m for m in منازل_list if s_منزل.strip().lower() in m.lower()]
        if sugg:
            chosen = st.selectbox("📌 اختر:", ["—"] + sugg[:6], key=f"sugg_م_{tab_key}")
            if chosen != "—":
                s_منزل = chosen
    if s_منتج:
        sugg = [p for p in produits_list if s_منتج.strip().lower() in p.lower()]
        if sugg:
            chosen = st.selectbox("📌 اختر:", ["—"] + sugg[:6], key=f"sugg_p_{tab_key}")
            if chosen != "—":
                s_منتج = chosen

    df_f = df.copy()
    if s_منزل and s_منزل != "—":
        df_f = df_f[df_f["المنزل"].str.contains(s_منزل, na=False, case=False)]
    if s_منتج and s_منتج != "—":
        df_f = df_f[df_f["المنتج"].str.contains(s_منتج, na=False, case=False)]
    if s_تاريخ:
        df_f = df_f[df_f["التاريخ"].str.contains(s_تاريخ, na=False)]

    if df_f.empty:
        st.info("لا توجد نتائج.")
        return

    for idx, row in df_f.iterrows():
        col_r, col_d = st.columns([5, 1])
        with col_r:
            st.write(f"**{row['التاريخ']}** | {row.get('النوع','')} | {row['المنزل']} | {row['المنتج']} | {row['الصنف']} | {row['الكمية']}")
        with col_d:
            if st.button("🗑️", key=f"del_{tab_key}_{idx}"):
                st.session_state[f"confirm_{tab_key}_{idx}"] = True

        if st.session_state.get(f"confirm_{tab_key}_{idx}"):
            st.warning("⚠️ راك سور؟")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ تأكيد", key=f"yes_{tab_key}_{idx}", use_container_width=True):
                    delete_fn(idx)
                    st.session_state[f"confirm_{tab_key}_{idx}"] = False
                    st.rerun()
            with c2:
                if st.button("❌ إلغاء", key=f"no_{tab_key}_{idx}", use_container_width=True):
                    st.session_state[f"confirm_{tab_key}_{idx}"] = False
                    st.rerun()

    st.divider()
    csv = df_f.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ تحميل CSV", csv, f"سجل_{tab_key}.csv", "text/csv", key=f"csv_{tab_key}")

# ── تحميل البيانات
produits = load_produits()
منازل = load_منازل()
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
    col1, col2 = st.columns(2)
    with col1:
        produit_out = st.selectbox("المنتج", produits, key="out_prod")
    with col2:
        quantite_out = st.number_input("الكمية", min_value=1, step=1, key="out_qty")
    col3, col4 = st.columns(2)
    with col3:
        type_out = st.selectbox("النوع", types, key="out_type")
    with col4:
        nom_out = st.selectbox("المنزل", منازل, key="out_nom")
    date_out = st.date_input("📅 التاريخ", value=date.today(), key="out_date")
    time_out = st.time_input("🕐 الوقت", value=datetime.now().time(), key="out_time")
    sijil_out = f"{nom_out} / {produit_out}/{type_out}/{quantite_out}"
    st.info(f"📝 إخراج... {sijil_out}")
    if st.button("✅ تأكيد الإخراج", use_container_width=True):
        تاريخ = datetime.combine(date_out, time_out).strftime("%Y-%m-%d %H:%M")
        if save_operation(تاريخ, "إخراج", nom_out, produit_out, type_out, quantite_out, f"إخراج... {sijil_out}"):
            st.success(f"✅ تم الإخراج وحُفظ: {sijil_out}")

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
        type_in = st.selectbox("النوع", types, key="in_type")
    with col4:
        nom_in = st.selectbox("المنزل", منازل, key="in_nom")
    date_in = st.date_input("📅 التاريخ", value=date.today(), key="in_date")
    time_in = st.time_input("🕐 الوقت", value=datetime.now().time(), key="in_time")
    sijil_in = f"{nom_in} / {produit_in}/{type_in}/{quantite_in}"
    st.info(f"📝 استلام... {sijil_in}")
    if st.button("✅ تأكيد الاستلام", use_container_width=True):
        تاريخ = datetime.combine(date_in, time_in).strftime("%Y-%m-%d %H:%M")
        df_ops = get_df_ops()
        ناقص = 0
        if not df_ops.empty:
            df_m = df_ops[(df_ops["المنزل"]==nom_in)&(df_ops["المنتج"]==produit_in)&(df_ops["الصنف"]==type_in)]
            ناقص = df_m[df_m["النوع"]=="إخراج"]["الكمية"].sum() - df_m[df_m["النوع"]=="استلام"]["الكمية"].sum() - quantite_in
        if save_operation(تاريخ, "استلام", nom_in, produit_in, type_in, quantite_in, f"استلام... {sijil_in}"):
            if ناقص > 0:
                st.warning(f"⚠️ تم الاستلام لكن هناك ناقص: {int(ناقص)} قطعة")
            else:
                st.success(f"✅ تم الاستلام وحُفظ: {sijil_in}")

# ── البيع
with tab3:
    st.markdown("### 🛒 تسجيل بيع")
    col1, col2 = st.columns(2)
    with col1:
        produit_v = st.selectbox("المنتج", produits, key="v_prod")
    with col2:
        quantite_v = st.number_input("الكمية", min_value=1, step=1, key="v_qty")
    type_v = st.selectbox("النوع", types, key="v_type")
    date_v = st.date_input("📅 التاريخ", value=date.today(), key="v_date")
    time_v = st.time_input("🕐 الوقت", value=datetime.now().time(), key="v_time")
    st.info(f"📝 بيع... {produit_v}/{type_v}/{quantite_v}")
    if st.button("✅ تأكيد البيع", use_container_width=True):
        تاريخ = datetime.combine(date_v, time_v).strftime("%Y-%m-%d %H:%M")
        if save_vente(تاريخ, produit_v, type_v, quantite_v):
            st.success(f"✅ تم تسجيل البيع وخرج من المخزون!")

    st.divider()
    st.markdown("#### 📜 سجل المبيعات")
    df_ventes = get_df_ventes()
    if not df_ventes.empty:
        st.dataframe(df_ventes[["التاريخ","المنتج","الصنف","الكمية"]], use_container_width=True)
        st.divider()
        for idx, row in df_ventes.iterrows():
            col_r, col_d = st.columns([5, 1])
            with col_r:
                st.write(f"**{row['التاريخ']}** | {row['المنتج']} | {row['الصنف']} | {row['الكمية']}")
            with col_d:
                if st.button("🗑️", key=f"del_v_{idx}"):
                    st.session_state[f"confirm_v_{idx}"] = True
            if st.session_state.get(f"confirm_v_{idx}"):
                st.warning("⚠️ راك سور؟")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ تأكيد", key=f"yes_v_{idx}", use_container_width=True):
                        delete_vente(idx)
                        st.session_state[f"confirm_v_{idx}"] = False
                        st.rerun()
                with c2:
                    if st.button("❌ إلغاء", key=f"no_v_{idx}", use_container_width=True):
                        st.session_state[f"confirm_v_{idx}"] = False
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

# ── الأخطاء
with tab5:
    st.markdown("### ❌ سجل الأخطاء (الناقص فقط)")
    df_ops = get_df_ops()
    if not df_ops.empty:
        rows = []
        for منزل in df_ops["المنزل"].unique():
            for منتج in df_ops[df_ops["المنزل"]==منزل]["المنتج"].unique():
                for صنف in df_ops[(df_ops["المنزل"]==منزل)&(df_ops["المنتج"]==منتج)]["الصنف"].unique():
                    df_f = df_ops[(df_ops["المنزل"]==منزل)&(df_ops["المنتج"]==منتج)&(df_ops["الصنف"]==صنف)]
                    خ = df_f[df_f["النوع"]=="إخراج"]["الكمية"].sum()
                    س = df_f[df_f["النوع"]=="استلام"]["الكمية"].sum()
                    ن = max(0, خ - س)
                    if ن > 0:
                        rows.append({"المنزل":منزل,"المنتج":منتج,"الصنف":صنف,"المُخرَج":int(خ),"المُستلَم":int(س),"الناقص":int(ن)})
        if rows:
            df_err = pd.DataFrame(rows)
            st.dataframe(df_err, use_container_width=True)
            csv_err = df_err.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ تحميل CSV", csv_err, "الأخطاء.csv", "text/csv")
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
            st.success(f"✅ تمت إضافة طلبية {liv_prod} / {liv_qty}")
            st.rerun()
    st.divider()
    livs = load_livraisons()
    if livs:
        for liv in livs:
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            with col1: st.write(f"**{liv['المنتج']}**")
            with col2: st.write(f"مطلوب: {liv['الكمية المطلوبة']}")
            with col3: st.write(f"إنتاج: {liv['في الإنتاج']}")
            with col4:
                btn_key = f"cancel_{liv['row_idx']
