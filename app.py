import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة والتنسيق الجمالي
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
        background-color: rgba(14, 17, 23, 0.92);
        z-index: 0;
    }
    .stApp > div {
        position: relative;
        z-index: 1;
    }
    .stButton>button { 
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }
    .warning-text { color: #ff4b4b; font-weight: bold; }
    .success-text { color: #4CAF50; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بجوجل شيت
@st.cache_resource
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

def get_data():
    sheet = get_sheet()
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_cols]
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def get_clients():
    """جلب قائمة العملاء من البيانات"""
    df = get_data()
    if not df.empty:
        unique_clients = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
        return unique_clients
    return []

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# 3. الواجهة الرئيسية
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    
    df = st.session_state.df
    clients_list = get_clients()

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والعملاء")
    with col_ref:
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_resource.clear()
            st.session_state.df = get_data()
            st.rerun()

    # إحصائيات سريعة
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 إجمالي المعاملات", len(df))
        with col2:
            st.metric("🏠 عدد العملاء", df['المنزل'].nunique())
        with col3:
            st.metric("📦 عدد المنتجات", df['المنتج'].nunique())
        with col4:
            total_qty = df['الكمية'].sum()
            st.metric("📈 إجمالي الكميات", f"{int(total_qty)}")

    tabs = st.tabs(["👥 العملاء", "📥 دخول", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز"])

    # --- TAB 0: إدارة العملاء ---
    with tabs[0]:
        st.subheader("👥 إدارة العملاء")
        
        st.markdown("### 🏠 العملاء الموجودون في النظام")
        if clients_list:
            st.write(f"عدد العملاء النشطين: {len(clients_list)}")
            for client in clients_list:
                st.text(f"• {client}")
        else:
            st.info("لا يوجد عملاء في النظام بعد")
        
        st.markdown("---")
        st.info("💡 ملاحظة: يمكن إضافة عملاء جدد عن طريق تسجيل دخول أو خروج باسم عميل جديد")

    # --- TAB 1: دخول ---
    with tabs[1]:
        st.subheader("📥 دخول بضاعة جديدة")
        with st.form("in_form"):
            f1, f2, f3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
            else:
                homes = []
                products = []

            in_home = f1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"], key="in_home")
            in_product = f2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"], key="in_product")
            in_qty = f3.number_input("الكمية", min_value=1, key="in_qty")
            
            # إضافة خيار لإدخال عميل جديد
            new_client = st.text_input("أو أدخل اسم عميل جديد (اختياري)")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
            with col_btn2:
                submitted = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submitted:
                final_client = new_client.strip() if new_client.strip() else in_home
                if in_qty > 0 and in_product.strip() and final_client != "لا توجد بيانات" and final_client:
                    append_row([in_qty, in_product, final_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success(f"✅ تم تسجيل الدخول بنجاح للعميل: {final_client}")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 2: إخراج ---
    with tabs[2]:
        st.subheader("📤 إخراج بضاعة جديدة")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
            else:
                homes = []
                products = []

            o_h = f1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"])
            o_p = f2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"])
            o_q = f3.number_input("الكمية", min_value=1)
            o_s = st.radio("نوع الخروج", ["ct (منزل كامل)", "fn (منزل ناقص)"], horizontal=True)
            o_s_value = "ct" if o_s.startswith("ct") else "fn"
            
            col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
            with col_btn2:
                submitted = st.form_submit_button("تسجيل الخروج", use_container_width=True)
            
            if submitted:
                if o_q > 0 and o_p.strip() and o_h.strip() and o_h != "لا توجد بيانات":
                    append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), o_s_value])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success(f"✅ تم تسجيل الخروج بنجاح (نوع: {o_s_value})")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 3: المخزن ---
    with tabs[3]:
        st.subheader("🏢 رصيد الشركة")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out_ct = df[df['الحالة'] == 'ct'].groupby('المنتج')['الكمية'].sum()
            s_out_fn = df[df['الحالة'] == 'fn'].groupby('المنتج')['الكمية'].sum()
            s_out = s_out_ct.add(s_out_fn, fill_value=0)
            stock = s_in.subtract(s_out, fill_value=0).reset_index()
            stock.columns = ['المنتج', 'الكمية']
            total_stock = stock['الكمية'].sum()
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("إجمالي الرصيد", f"{int(total_stock)} قطعة", delta="متوفر")
            
            if total_stock > 0:
                for _, r in stock.iterrows():
                    if r['الكمية'] > 0:
                        st.info(f"📦 {r['المنتج']}: {int(r['الكمية'])} قطعة متوفرة")
            else:
                st.warning("⚠️ المخزن فارغ حالياً")
        else:
            st.info("لا توجد بيانات")

    # --- TAB 4: كشف الحساب ---
    with tabs[4]:
        st.subheader("💰 كشف حساب العملاء")
        if not df.empty:
            pivot_table = df.pivot_table(
                index='المنزل', 
                columns='الحالة', 
                values='الكمية', 
                aggfunc='sum', 
                fill_value=0
            )
            
            # إعادة تسمية الأعمدة للتوضيح
            pivot_table = pivot_table.rename(columns={
                'st': 'دخول',
                'ct': 'خروج كامل',
                'fn': 'خروج ناقص'
            })
            
            # تحويل الأرقام إلى أعداد صحيحة
            pivot_table = pivot_table.astype(int)
            
            st.dataframe(pivot_table, use_container_width=True)
        else:
            st.info("لا توجد بيانات لعرضها")

    # --- TAB 5: History مع ألوان ---
    with tabs[5]:
        st.subheader("📜 سجل المعاملات (آخر 50)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50).copy()
            
            # تحويل الكمية إلى عدد صحيح
            history_df['الكمية'] = history_df['الكمية'].astype(int)
            
            # تنسيق التاريخ للعرض
            history_df['التاريخ'] = pd.to_datetime(history_df['التاريخ'], errors='coerce')
            history_df['التاريخ'] = history_df['التاريخ'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # إضافة عمود نوع العملية للعرض
            history_df['نوع العملية'] = history_df['الحالة'].map({
                'st': '📥 دخول',
                'ct': '📤 خروج كامل',
                'fn': '📤 خروج ناقص'
            }).fillna(history_df['الحالة'])
            
            # إنشاء DataFrame للعرض مع الألوان
            display_df = history_df[['المنزل', 'المنتج', 'الكمية', 'نوع العملية', 'التاريخ']].copy()
            
            # تلوين الصفوف حسب نوع العملية
            def color_rows(row):
                if row['نوع العملية'].startswith('📥'):
                    return ['background-color: #4CAF50; color: white'] * len(row)
                else:
                    return ['background-color: #ff4b4b; color: white'] * len(row)
            
            # عرض الجدول بالألوان
            styled_df = display_df.style.apply(color_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # إحصائيات سريعة
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                total_in = len(history_df[history_df['الحالة'] == 'st'])
                st.info(f"📥 عدد عمليات الدخول: {total_in}")
            with col_stat2:
                total_out = len(history_df[history_df['الحالة'].isin(['ct', 'fn'])])
                st.error(f"📤 عدد عمليات الخروج: {total_out}")
            
            # زر لتصدير البيانات
            csv = history_df[['المنزل', 'المنتج', 'الكمية', 'الحالة', 'التاريخ']].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل السجل كـ CSV",
                data=csv,
                file_name=f"history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info("السجل فارغ حالياً.")

    # --- TAB 6: إنجاز ---
    with tabs[6]:
        st.subheader("✅ إنجاز العملاء")
        if not df.empty:
            # حساب إجمالي الدخول لكل عميل
            total_in = df[df['الحالة'] == 'st'].groupby('المنزل')['الكمية'].sum()
            # حساب إجمالي الخروج لكل عميل
            total_out = df[df['الحالة'].isin(['ct', 'fn'])].groupby('المنزل')['الكمية'].sum()
            
            # دمج البيانات
            summary = pd.DataFrame({
                'العميل': total_in.index.union(total_out.index)
            })
            summary['مجموع الدخول'] = summary['العميل'].map(total_in).fillna(0).astype(int)
            summary['مجموع الخروج'] = summary['العميل'].map(total_out).fillna(0).astype(int)
            summary['الرصيد'] = (summary['مجموع الدخول'] - summary['مجموع الخروج']).astype(int)
            summary['عدد المنتجات'] = df.groupby('المنزل')['المنتج'].nunique().map(summary.set_index('العميل')['عدد المنتجات']).fillna(0).astype(int)
            
            # إعادة ترتيب الأعمدة
            summary = summary[['العميل', 'عدد المنتجات', 'مجموع الدخول', 'مجموع الخروج', 'الرصيد']]
            
            # تلوين الصفوف التي رصيدها صفر
            def highlight_zero(row):
                if row['الرصيد'] == 0:
                    return ['background-color: #4CAF50; color: white; font-weight: bold'] * len(row)
                elif row['الرصيد'] < 0:
                    return ['background-color: #ff4b4b; color: white; font-weight: bold'] * len(row)
                return [''] * len(row)

            st.dataframe(
                summary.style.apply(highlight_zero, axis=1),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "العميل": "العميل",
                    "عدد المنتجات": st.column_config.NumberColumn("عدد المنتجات", format="%d"),
                    "مجموع الدخول": st.column_config.NumberColumn("مجموع الدخول", format="%d"),
                    "مجموع الخروج": st.column_config.NumberColumn("مجموع الخروج", format="%d"),
                    "الرصيد": st.column_config.NumberColumn("الرصيد", format="%d")
                }
            )
            
            # إضافة إحصائية سريعة
            st.markdown("---")
            total_clients = len(summary)
            completed_clients = len(summary[summary['الرصيد'] == 0])
            negative_clients = len(summary[summary['الرصيد'] < 0])
            positive_clients = len(summary[summary['الرصيد'] > 0])
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.success(f"✅ عملاء منجزون (رصيد 0): {completed_clients}")
            with col_stat2:
                st.warning(f"⚠️ عملاء عليهم دين (رصيد -): {negative_clients}")
            with col_stat3:
                st.info(f"📦 عملاء لديهم رصيد: {positive_clients}")
            
        else:
            st.info("لا توجد بيانات حالياً.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    st.exception(e)
