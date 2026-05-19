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
BASE_IMAGE_URL = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images/"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_resource
def get_spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)

def get_worksheet(name):
    return get_spreadsheet().worksheet(name)

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
    types = [col.strip() for col in df.columns[1:] if col.strip() != ""]
    return types if types else ["FN", "CT"]

@st.cache_data(ttl=60)
def load_منازل():
    df = load_sheet_csv("السلع")
    col_a = df.iloc[:, 0].dropna()
    col_a = col_a[col_a.str.strip() != ""]
    return col_a.tolist()

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
        if len(ws.get_all_values()) == 0:
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
        ws.delete_rows(row_idx + 2)  # +2 لأن الصف الأول عناوين والindex يبدأ من 0
        load_operations.clear()
        return True
    except Exception as e:
        st.warning(f"⚠️ خطأ في الحذف: {e}")
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
    except:
        return pd.DataFrame(columns=["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])

def save_vente(تاريخ, منزل, منتج, صنف, كمية, سجل):
    try:
        ws = get_worksheet("البيع")
        if len(ws.get_all_values()) == 0:
            ws.append_row(["التاريخ","النوع","المنزل","المنتج","الصنف","الكمية","السجل"])
        ws.append_row([تاريخ, "بيع", منزل, منتج, صنف, int(كمية), سجل])
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
                    "الحالة": row[3]
                })
        return livs
    except:
        return []

def save_livraison(منتج, كمية):
    try:
        ws = get_worksheet("No Livrai")
        if len(ws.get_all_values()) == 0:
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
        df = df[df["المرجع"].str.strip() != ""]
        df = df[df["الرابط"].str.strip() != ""]
        return df
    except:
        return pd.DataFrame(columns=["المرجع", "الرابط"])

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

# ── helper: بحث مع اقتراحات
def search_with_suggestions(label, options, key):
    query = st.text_input(label, key=key)
    if query:
        suggestions = [o for o in options if query.strip().lower() in o.lower()]
        if suggestions and query not in suggestions:
            chosen = st.selectbox("اقتراحات:", ["— اختر —"] + suggestions, key=key + "_sug")
            if chosen != "— اختر —":
                return chosen
    return query

produits = load_produits()
منازل = load_منازل()
types = load_types()

if st.button("🔄 تحديث جميع البيانات", use_container_width=True):
    load_produits.clear()
    load_منازل.clear()
    load_types.clear()
    load_operations.clear()
    load_ventes.clear()
    load_livraisons.clear()
    load_images.clear()
    load_sheet_csv.clear()
    st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📤 إخراج", "📥 استلام", "🛒 البيع", "🏪 المخزن", "❌ الأخطاء", "📦 No Livraison", "🖼️ الصور"
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
        تاريخ_كامل = datetime.combine(date_out, time_out).strftime("%Y-%m-%d %H:%M")
        if save_operation(تاريخ_كامل, "إخراج", nom_out, produit_out, type_out, quantite_out, f"إخراج... {sijil_out}"):
            st.success(f"✅ تم الإخراج وحُفظ: {sijil_out} — {تاريخ_كامل}")

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
        تاريخ_كامل = datetime.combine(date_in, time_in).strftime("%Y-%m-%d %H:%M")
        df_ops = get_df_ops()
        if not df_ops.empty:
            df_منزل = df_ops[
                (df_ops["المنزل"] == nom_in) &
                (df_ops["المنتج"] == produit_in) &
                (df_ops["الصنف"] == type_in)
            ]
            اخراج = df_منزل[df_منزل["النوع"] == "إخراج"]["الكمية"].sum()
            استلام_سابق = df_منزل[df_منزل["النوع"] == "استلام"]["الكمية"].sum()
            ناقص = اخراج - استلام_سابق - quantite_in
        else:
            ناقص = 0
        if save_operation(تاريخ_كامل, "استلام", nom_in, produit_in, type_in, quantite_in, f"استلام... {sijil_in}"):
            if ناقص > 0:
                st.warning(f"⚠️ تم الاستلام لكن هناك ناقص: {int(ناقص)} قطعة")
            else:
                st.success(f"✅ تم الاستلام وحُفظ: {sijil_in} — {تاريخ_كامل}")

# ── البيع
with tab3:
    st.markdown("### 🛒 البيع — تسليم للعميل")
    col1, col2 = st.columns(2)
    with col1:
        produit_vente = st.selectbox("المنتج", produits, key="vente_prod")
    with col2:
        quantite_vente = st.number_input("الكمية", min_value=1, step=1, key="vente_qty")
    col3, col4 = st.columns(2)
    with col3:
        type_vente = st.selectbox("النوع", types, key="vente_type")
    with col4:
        nom_vente = st.selectbox("المنزل", منازل, key="vente_nom")
    date_vente = st.date_input("📅 التاريخ", value=date.today(), key="vente_date")
    time_vente = st.time_input("🕐 الوقت", value=datetime.now().time(), key="vente_time")
    sijil_vente = f"{nom_vente} / {produit_vente}/{type_vente}/{quantite_vente}"
    st.info(f"📝 بيع... {sijil_vente}")

    if st.button("🛒 تأكيد البيع", use_container_width=True):
        st.session_state["confirm_vente"] = True
        st.session_state["vente_data"] = {
            "تاريخ": datetime.combine(date_vente, time_vente).strftime("%Y-%m-%d %H:%M"),
            "منزل": nom_vente, "منتج": produit_vente,
            "صنف": type_vente, "كمية": quantite_vente, "سجل": f"بيع... {sijil_vente}"
        }

    if st.session_state.get("confirm_vente"):
        st.warning("⚠️ راك سور؟ متتمنيكش إذا فاصيت متوليش!")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ تأكيد", use_container_width=True, key="yes_vente"):
                d = st.session_state["vente_data"]
                if save_vente(d["تاريخ"], d["منزل"], d["منتج"], d["صنف"], d["كمية"], d["سجل"]):
                    st.success(f"✅ تم البيع وحُفظ! {sijil_vente}")
                st.session_state["confirm_vente"] = False
                st.rerun()
        with col_no:
            if st.button("❌ إلغاء", use_container_width=True, key="no_vente"):
                st.session_state["confirm_vente"] = False
                st.rerun()

    st.divider()
    st.markdown("#### 📜 سجل المبيعات")
    df_ventes = get_df_ventes()

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        sv_منزل = st.text_input("🔍 بحث بالمنزل", key="sv_منزل")
    with col_s2:
        sv_منتج = st.text_input("🔍 بحث بالمنتج", key="sv_منتج")
    with col_s3:
        sv_تاريخ = st.text_input("📅 بحث بالتاريخ", placeholder="2026-05-19", key="sv_تاريخ")

    # اقتراحات البحث
    if sv_منزل:
        sugg = [m for m in منازل if sv_منزل.strip().lower() in m.lower()]
        if sugg:
            st.caption("اقتراحات: " + " | ".join(sugg[:5]))
    if sv_منتج:
        sugg = [p for p in produits if sv_منتج.strip().lower() in p.lower()]
        if sugg:
            st.caption("اقتراحات: " + " | ".join(sugg[:5]))

    if not df_ventes.empty:
        df_vf = df_ventes.copy()
        if sv_منزل:
            df_vf = df_vf[df_vf["المنزل"].str.contains(sv_منزل, na=False)]
        if sv_منتج:
            df_vf = df_vf[df_vf["المنتج"].str.contains(sv_منتج, na=False)]
        if sv_تاريخ:
            df_vf = df_vf[df_vf["التاريخ"].str.contains(sv_تاريخ, na=False)]

        for idx, row in df_vf.iterrows():
            col_r, col_d = st.columns([5, 1])
            with col_r:
                st.write(f"**{row['التاريخ']}** | {row['المنزل']} | {row['المنتج']} | {row['الصنف']} | {row['الكمية']}")
            with col_d:
                if st.button("🗑️", key=f"del_vente_{idx}"):
                    st.session_state[f"confirm_del_vente_{idx}"] = True

            if st.session_state.get(f"confirm_del_vente_{idx}"):
                st.warning("⚠️ راك سور؟ متتمنيكش إذا فاصيت متوليش!")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ تأكيد الحذف", key=f"yes_del_vente_{idx}", use_container_width=True):
                        delete_vente(idx)
                        st.session_state[f"confirm_del_vente_{idx}"] = False
                        st.rerun()
                with c2:
                    if st.button("❌ إلغاء", key=f"no_del_vente_{idx}", use_container_width=True):
                        st.session_state[f"confirm_del_vente_{idx}"] = False
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
        df_out = df_ops[df_ops["النوع"] == "إخراج"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
        df_out.columns = ["المنزل","المنتج","الصنف","المُخرَج"]
        df_in = df_ops[df_ops["النوع"] == "استلام"].groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
        df_in.columns = ["المنزل","المنتج","الصنف","المُستلَم"]
        df_balance = df_out.merge(df_in, on=["المنزل","المنتج","الصنف"], how="left")
        df_balance["المُستلَم"] = df_balance["المُستلَم"].fillna(0).astype(int)

        # خصم المبيعات من المخزون
        if not df_ventes.empty:
            df_sold = df_ventes.groupby(["المنزل","المنتج","الصنف"])["الكمية"].sum().reset_index()
            df_sold.columns = ["المنزل","المنتج","الصنف","المباع"]
            df_balance = df_balance.merge(df_sold, on=["المنزل","المنتج","الصنف"], how="left")
            df_balance["المباع"] = df_balance["المباع"].fillna(0).astype(int)
        else:
            df_balance["المباع"] = 0

        df_balance["الرصيد المتبقي"] = df_balance["المُستلَم"] - df_balance["المباع"]
        st.dataframe(df_balance, use_container_width=True)

        st.divider()
        st.markdown("#### 📜 كل السجلات (مرتبة زمنياً)")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            search_منزل = st.text_input("🔍 بحث بالمنزل", key="s_منزل")
        with col_s2:
            search_منتج = st.text_input("🔍 بحث بالمنتج", key="s_منتج")
        with col_s3:
            search_تاريخ = st.text_input("📅 بحث بالتاريخ", placeholder="2026-05-19", key="s_تاريخ")

        # اقتراحات
        if search_منزل:
            sugg = [m for m in منازل if search_منزل.strip().lower() in m.lower()]
            if sugg:
                st.caption("اقتراحات: " + " | ".join(sugg[:5]))
        if search_منتج:
            sugg = [p for p in produits if search_منتج.strip().lower() in p.lower()]
            if sugg:
                st.caption("اقتراحات: " + " | ".join(sugg[:5]))

        df_filtered = df_ops.copy()
        if search_منزل:
            df_filtered = df_filtered[df_filtered["المنزل"].str.contains(search_منزل, na=False)]
        if search_منتج:
            df_filtered = df_filtered[df_filtered["المنتج"].str.contains(search_منتج, na=False)]
        if search_تاريخ:
            df_filtered = df_filtered[df_filtered["التاريخ"].str.contains(search_تاريخ, na=False)]

        for idx, row in df_filtered.iterrows():
            col_r, col_d = st.columns([5, 1])
            with col_r:
                st.write(f"**{row['التاريخ']}** | {row['النوع']} | {row['المنزل']} | {row['المنتج']} | {row['الصنف']} | {row['الكمية']}")
            with col_d:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state[f"confirm_del_{idx}"] = True

            if st.session_state.get(f"confirm_del_{idx}"):
                st.warning("⚠️ راك سور؟ متتمنيكش إذا فاصيت متوليش!")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ تأكيد الحذف", key=f"yes_del_{idx}", use_container_width=True):
                        delete_operation(idx)
                        st.session_state[f"confirm_del_{idx}"] = False
                        st.rerun()
                with c2:
                    if st.button("❌ إلغاء", key=f"no_del_{idx}", use_container_width=True):
                        st.session_state[f"confirm_del_{idx}"] = False
                        st.rerun()

        st.divider()
        csv = df_filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ تحميل CSV", csv, "سجل_العمليات.csv", "text/csv")
    else:
        st.info("المخزن فارغ — سجّل أول عملية.")

# ── الأخطاء
with tab5:
    st.markdown("### ❌ سجل الأخطاء (الناقص فقط)")
    df_ops = get_df_ops()
    if not df_ops.empty:
        rows = []
        for منزل in df_ops["المنزل"].unique():
            for منتج in df_ops[df_ops["المنزل"] == منزل]["المنتج"].unique():
                for صنف in df_ops[
                    (df_ops["المنزل"] == منزل) &
                    (df_ops["المنتج"] == منتج)
                ]["الصنف"].unique():
                    df_f = df_ops[
                        (df_ops["المنزل"] == منزل) &
                        (df_ops["المنتج"] == منتج) &
                        (df_ops["الصنف"] == صنف)
                    ]
                    اخراج_كلي = df_f[df_f["النوع"] == "إخراج"]["الكمية"].sum()
                    استلام_كلي = df_f[df_f["النوع"] == "استلام"]["الكمية"].sum()
                    ناقص_حالي = max(0, اخراج_كلي - استلام_كلي)
                    if ناقص_حالي > 0:
                        rows.append({
                            "المنزل": منزل, "المنتج": منتج, "الصنف": صنف,
     
