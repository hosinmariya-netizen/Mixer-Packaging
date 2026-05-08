import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
        direction: rtl;
        background-image: url("https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(14, 17, 23, 0.90);
        z-index: 0;
    }
    .stButton>button { border-radius: 10px; }
    .warning-text { color: #ff4b4b; font-weight: bold; padding: 10px; border: 1px solid #ff4b4b; border-radius: 5px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background-color: #333; color: white; padding: 6px; text-align: center; }
    tr:nth-child(odd) { background-color: #D6C1A6; color: black; }
    tr:nth-child(even) { background-color: #ffa500; color: black; }
    td { padding: 5px 8px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
    return sheet.sheet1

def get_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def append_row(row):
    sheet = get_sheet()
    sheet.append_row(row)

def update_row_qty(sheet, row_index, new_qty):
    sheet.update_cell(row_index + 2, 1, new_qty)

try:
    df = get_data()
    df.columns = df.columns.str.strip()
    if 'الكمية' in df.columns:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة والاستلام")
    with col_ref:
        if st.button("🔄 تحديث البيانات"):
            st.cache_resource.clear()
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 استلام من المنازل", "📤 إخراج للمنزل", "🏢 المخزن النهائي", "📋 History", "💰 كشف الحساب"])

    with tab1:
        st.subheader("📦 إدارة المستلمات من المنازل")
        homes = [h for h in df['المنزل'].unique() if h != "-"]

        for home in homes:
            home_data = df[df['المنزل'] == home]
            prods = home_data['المنتج'].unique()

            pending_count = 0
            total_remaining = 0
            for prod in prods:
                p_data = home_data[home_data['المنتج'] == prod]
                total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                already_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                remaining = total_out - already_in
                if remaining > 0:
                    pending_count += 1
                    total_remaining += remaining

            badge = f"🟢 {pending_count}" if pending_count > 0 else "🔴 0"
            label = f"🏠 منزل: {home}  {badge}  |  📦 {int(total_remaining)}"

            with st.expander(label):
                for prod in prods:
                    p_data = home_data[home_data['المنتج'] == prod]
                    total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                    already_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    max_allowed = total_out - already_in

                    if max_allowed > 0:
                        st.markdown(f"--- \n **المنتج:** {prod}")
                        c1, c2, c3 = st.columns([2, 2, 1])
                        with c1:
                            input_qty = st.number_input(f"الكمية المستلمة (الحد الأقصى {int(max_allowed)})",
                                                       min_value=0, step=1, key=f"qty_{home}_{prod}")
                        is_over = input_qty > max_allowed
                        ignore_warning = False
                        if is_over:
                            st.markdown(f'<p class="warning-text">⚠️ تحذير: الكمية ({int(input_qty)}) أكبر من الصادرة ({int(max_allowed)})!</p>', unsafe_allow_html=True)
                            ignore_warning = st.checkbox("تجاهل التحذير", key=f"ign_{home}_{prod}")
                        with c2:
                            btn_disabled = is_over and not ignore_warning
                            if st.button(f"✓ تأكيد الاستلام", key=f"btn_{home}_{prod}", disabled=btn_disabled):
                                if input_qty > 0:
                                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    append_row([input_qty, prod, home, now, "st"])
                                    st.cache_resource.clear()
                                    st.success("تم تسجيل الاستلام بنجاح!")
                                    st.rerun()
                    else:
                        st.caption(f"✅ {prod}: تم استلام كامل الكمية الصادرة.")

    with tab2:
        st.subheader("📤 إخراج بضاعة للمنزل")
        homes = [h for h in df['المنزل'].unique() if h != "-"]
        all_prods = df['المنتج'].unique().tolist()

        col1, col2, col3 = st.columns(3)
        with col1:
            out_home = st.selectbox("اختر المنزل", homes, key="out_home")
        with col2:
            out_prod = st.selectbox("اختر المنتج", all_prods, key="out_prod")
        with col3:
            out_qty = st.number_input("الكمية", min_value=1, step=1, key="out_qty")

        out_status = st.radio("نوع الإخراج", ["ct", "fn"], horizontal=True, key="out_status")

        if st.button("📤 تأكيد الإخراج"):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            append_row([out_qty, out_prod, out_home, now, out_status])
            st.cache_resource.clear()
            st.success(f"تم تسجيل إخراج {int(out_qty)} من {out_prod} للمنزل {out_home}")
            st.rerun()

    with tab3:
        st.subheader("🏢 رصيد الشركة الحالي")
        stock_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        stock_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        stock_final = stock_in.subtract(stock_out, fill_value=0).reset_index()
        stock_final.columns = ['اسم المنتج', 'المخزن']
        stock_final['المخزن'] = stock_final['المخزن'].astype(int)

        for _, row in stock_final.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['اسم المنتج']}**")
            with col2:
                st.write(f"{row['المخزن']}")
            with col3:
                if st.button(f"✅ تسليم للعميل", key=f"cl_{row['اسم المنتج']}"):
                    qty_to_remove = st.session_state.get(f"cl_qty_{row['اسم المنتج']}", 0)
                    if qty_to_remove > 0:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        append_row([qty_to_remove, row['اسم المنتج'], "-", now, "cl"])
                        st.cache_resource.clear()
                        st.rerun()
            st.number_input("الكمية المسلمة للعميل", min_value=0, step=1, key=f"cl_qty_{row['اسم المنتج']}")
            st.divider()

    with tab4:
        st.subheader("📋 سجل العمليات")
        history = df[df['الحالة'].isin(['ct', 'fn', 'st'])].copy()
        history['الكمية'] = history['الكمية'].astype(int)

        rows_html = ""
        for i, (idx, row) in enumerate(history.iterrows()):
            color = "#D6C1A6" if i % 2 == 0 else "#ffa500"
            checked = st.checkbox("↩️", key=f"hist_{idx}")
            if checked:
                sheet = get_sheet()
                sheet.update_cell(idx + 2, 1, 0)
                st.cache_resource.clear()
                st.success(f"تم إرجاع الكمية للصفر")
                st.rerun()
            rows_html += f"""
            <tr style="background-color:{color}">
                <td>{row['المنزل']}</td>
                <td>{row['المنتج']}</td>
                <td>{row['الحالة']}</td>
                <td>{row['الكمية']}</td>
                <td>{row.get('التاريخ','')}</td>
            </tr>"""

        st.markdown(f"""
        <table>
            <tr>
                <th>المنزل</th>
                <th>المنتج</th>
                <th>النوع</th>
                <th>الكمية</th>
                <th>التاريخ</th>
            </tr>
            {rows_html}
        </table>
        """, unsafe_allow_html=True)

    with tab5:
        st.subheader("💰 ملخص العمليات المنجزة للدفع")
        payment_summary = df[df['الحالة'].isin(['ct', 'fn'])].groupby(['المنزل', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
        st.dataframe(payment_summary, use_container_width=True)

except Exception as e:
    st.error(f"خطأ في البيانات: {e}")
