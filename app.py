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
    """جلب قائمة العملاء من ورقة منفصلة أو من البيانات"""
    sheet = get_sheet()
    if sheet:
        try:
            # محاولة فتح ورقة العملاء
            clients_sheet = sheet.client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").worksheet("العملاء")
            data = clients_sheet.get_all_records()
            clients_df = pd.DataFrame(data)
            return clients_df
        except:
            # إذا لم توجد ورقة عملاء، نستخدم العملاء الموجودين في البيانات الرئيسية
            df = get_data()
            if not df.empty:
                unique_clients = df['المنزل'].unique()
                clients_df = pd.DataFrame({
                    'اسم العميل': unique_clients,
                    'النوع': ''  # فارغ ليختار المستخدم
                })
                return clients_df
            return pd.DataFrame(columns=['اسم العميل', 'النوع'])
    return pd.DataFrame(columns=['اسم العميل', 'النوع'])

def add_client(client_name, client_type):
    """إضافة عميل جديد"""
    sheet = get_sheet()
    if sheet:
        try:
            clients_sheet = sheet.client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").worksheet("العملاء")
            clients_sheet.append_row([client_name, client_type])
        except:
            # إنشاء ورقة عملاء جديدة إذا لم توجد
            clients_sheet = sheet.client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso").add_worksheet(title="العملاء", rows=100, cols=2)
            clients_sheet.append_row(["اسم العميل", "النوع"])
            clients_sheet.append_row([client_name, client_type])

def update_client(old_name, new_name, new_type):
    """تعديل عميل"""
    # هذه وظيفة متقدمة تحتاج إلى معالجة خاصة
    pass

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# 3. الواجهة الرئيسية
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    if "clients_df" not in st.session_state:
        st.session_state.clients_df = get_clients()
    
    df = st.session_state.df
    clients_df = st.session_state.clients_df

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والعملاء")
    with col_ref:
        if st.button("🔄 تحديث", use_container_width=True):
            st.cache_resource.clear()
            st.session_state.df = get_data()
            st.session_state.clients_df = get_clients()
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

    # --- TAB 0: إدارة العملاء (جديد) ---
    with tabs[0]:
        st.subheader("👥 إدارة العملاء")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ➕ إضافة عميل جديد")
            with st.form("add_client_form"):
                new_client_name = st.text_input("اسم العميل")
                new_client_type = st.selectbox("نوع العميل", ["ct (كامل)", "fn (ناقص)"])
                new_client_type_value = "ct" if "ct" in new_client_type else "fn"
                
                if st.form_submit_button("إضافة عميل", use_container_width=True):
                    if new_client_name.strip():
                        # التحقق من عدم وجود العميل مسبقاً
                        if new_client_name not in clients_df['اسم العميل'].values:
                            add_client(new_client_name, new_client_type_value)
                            st.session_state.clients_df = get_clients()
                            st.success(f"✅ تم إضافة العميل {new_client_name}")
                            st.rerun()
                        else:
                            st.warning("⚠️ هذا العميل موجود مسبقاً")
                    else:
                        st.warning("⚠️ يرجى إدخال اسم العميل")
        
        with col2:
            st.markdown("### 📋 قائمة العملاء")
            if not clients_df.empty and len(clients_df) > 0:
                # عرض العملاء مع ألوان حسب النوع
                clients_display = clients_df.copy()
                clients_display['النوع'] = clients_display['النوع'].map({
                    'ct': '🟢 كامل (CT)',
                    'fn': '🟡 ناقص (FN)'
                }).fillna('⚪ غير محدد')
                st.dataframe(clients_display, use_container_width=True, hide_index=True)
                
                # إحصائيات العملاء
                col_a, col_b = st.columns(2)
                with col_a:
                    ct_count = len(clients_df[clients_df['النوع'] == 'ct'])
                    st.info(f"🟢 عملاء CT (كامل): {ct_count}")
                with col_b:
                    fn_count = len(clients_df[clients_df['النوع'] == 'fn'])
                    st.warning(f"🟡 عملاء FN (ناقص): {fn_count}")
            else:
                st.info("لا يوجد عملاء مضافون حالياً")
        
        # عرض العملاء من البيانات الرئيسية
        st.markdown("---")
        st.markdown("### 🏠 العملاء الموجودون في النظام")
        if not df.empty:
            existing_clients = df['المنزل'].unique()
            st.write(f"عدد العملاء النشطين: {len(existing_clients)}")
            for client in existing_clients:
                st.text(f"• {client}")
        else:
            st.info("لا يوجد عملاء في النظام بعد")

    # --- TAB 1: دخول ---
    with tabs[1]:
        st.subheader("📥 دخول بضاعة جديدة")
        with st.form("in_form"):
            f1, f2, f3 = st.columns(3)
            
            # استخدام قائمة العملاء من ورقة العملاء
            if not clients_df.empty and len(clients_df) > 0:
                homes = clients_df['اسم العميل'].tolist()
            elif not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
            else:
                homes = []
            
            products = [p for p in df['المنتج'].unique() if p not in ["", "-"]] if not df.empty else []

            in_home = f1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"], key="in_home")
            in_product = f2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"], key="in_product")
            in_qty = f3.number_input("الكمية", min_value=1, key="in_qty")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
            with col_btn2:
                submitted = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submitted:
                if in_qty > 0 and in_product.strip() and in_home.strip() and in_home != "لا توجد بيانات":
                    append_row([in_qty, in_product, in_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success("✅ تم تسجيل الدخول بنجاح")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 2: إخراج ---
    with tabs[2]:
        st.subheader("📤 إخراج بضاعة جديدة")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            
            # استخدام قائمة العملاء من ورقة العملاء
            if not clients_df.empty and len(clients_df) > 0:
                homes = clients_df['اسم العميل'].tolist()
            elif not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
            else:
                homes = []
            
            products = [p for p in df['المنتج'].unique() if p not in ["", "-"]] if not df.empty else []

            o_h = f1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"])
            o_p = f2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"])
            o_q = f3.number_input("الكمية", min_value=1)
            
            # تحديد نوع العميل تلقائياً من قائمة العملاء
            default_type = "ct"
            if not clients_df.empty and o_h in clients_df['اسم العميل'].values:
                client_type = clients_df[clients_df['اسم العميل'] == o_h]['النوع'].values[0]
                if client_type == 'ct':
                    st.info(f"🟢 هذا العميل من نوع CT (كامل)")
                    default_type = "ct"
                elif client_type == 'fn':
                    st.warning(f"🟡 هذا العميل من نوع FN (ناقص)")
                    default_type = "fn"
            
            o_s_value = default_type
            
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
            
            # إعادة تسمية أعمدة الحالة للتوضيح
            history_df['نوع العملية'] = history_df['الحالة'].map({
                'st': 'دخول',
                'ct': 'خروج كامل',
                'fn': 'خروج ناقص'
            }).fillna(history_df['الحالة'])
            
            # تلوين الصفوف حسب نوع العملية
            def color_rows(row):
                if row['الحالة'] == 'st':
                    return ['background-color: #4CAF50; color: white'] * len(row)
                else:
                    return ['background-color: #ff4b4b; color: white'] * len(row)
            
            # عرض الجدول بالألوان
            st.dataframe(
                history_df[['المنزل', 'المنتج', 'الكمية', 'نوع العملية', 'التاريخ']].style.apply(color_rows, axis=1),
                use_container_width=True,
                column_config={
                    "المنزل": "العميل",
                    "المنتج": "المنتج", 
                    "الكمية": st.column_config.NumberColumn("الكمية", format="%d"),
                    "نوع العملية": "نوع العملية",
                    "التاريخ": "التاريخ"
                }
            )
            
            # إحصائيات سريعة
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                total_in = len(history_df[history_df['الحالة'] == 'st'])
                st.info(f"📥 عدد عمليات الدخول: {total_in}")
            with col_stat2:
                total_out = len(history_df[history_df['الحالة'].isin(['ct', 'fn'])])
                st.error(f"📤 عدد عمليات الخروج: {total_out}")
            
            # زر لتصدير البيانات
            csv = history_df[['المنزل', 'المنتج', 'الكمية', 'نوع العملية', 'التاريخ']].to_csv(index=False).encode('utf-8-sig')
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
            summary = df.groupby("المنزل").agg(
                عدد_المنتجات=("المنتج", "nunique"),
                مجموع_الكمية=("الكمية", "sum")
            ).reset_index()
            
            # تحويل إلى أعداد صحيحة
            summary['مجموع_الكمية'] = summary['مجموع_الكمية'].fillna(0).astype(int)
            summary['عدد_المنتجات'] = summary['عدد_المنتجات'].fillna(0).astype(int)

            # إضافة نوع العميل إن وجد
            if not clients_df.empty:
                summary = summary.merge(clients_df, left_on='المنزل', right_on='اسم العميل', how='left')
                summary['النوع'] = summary['النوع'].fillna('غير محدد')
                summary['النوع'] = summary['النوع'].map({
                    'ct': '🟢 كامل',
                    'fn': '🟡 ناقص'
                }).fillna('⚪ غير محدد')
            else:
                summary['النوع'] = ''

            # تلوين الصفوف التي مجموعها صفر باللون الأحمر
            def highlight_zero(row):
                if row['مجموع_الكمية'] == 0:
                    return ['background-color: #ff4b4b; color: white; font-weight: bold'] * len(row)
                return [''] * len(row)

            st.dataframe(
                summary[['المنزل', 'عدد_المنتجات', 'مجموع_الكمية', 'النوع']].style.apply(highlight_zero, axis=1),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "المنزل": "العميل",
                    "عدد_المنتجات": st.column_config.NumberColumn("عدد المنتجات", format="%d"),
                    "مجموع_الكمية": st.column_config.NumberColumn("مجموع الكمية", format="%d"),
                    "النوع": "نوع العميل"
                }
            )
            
            # إضافة إحصائية سريعة
            st.markdown("---")
            total_homes = len(summary)
            completed_homes = len(summary[summary['مجموع_الكمية'] == 0])
            st.info(f"📊 من أصل {total_homes} عميل، {completed_homes} عميل منجز (مجموع الكمية = 0)")
            
        else:
            st.info("لا توجد بيانات حالياً.")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    st.exception(e)
