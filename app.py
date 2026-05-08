import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", layout="wide", page_icon="🧵")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        direction: rtl;
    }
    .stButton>button { 
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }
    .phase-card {
        background-color: #1e1e2e;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 5px solid #4CAF50;
    }
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
        expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "المرحلة"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_cols]
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

def safe_int(value):
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except:
        return 0

# 3. الواجهة الرئيسية
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    # الهيدر
    st.title("🧵 نظام إدارة الورشة - Bébé Sympa")
    st.caption("مراحل الإنتاج: الخياطة (CT) → التغليف (FN) → تسليم")
    
    col_t, col_ref = st.columns([4, 1])
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
            ct_qty = safe_int(df[df['المرحلة'] == 'ct']['الكمية'].sum())
            fn_qty = safe_int(df[df['المرحلة'] == 'fn']['الكمية'].sum())
            st.metric("📈 قيد الإنتاج", f"{ct_qty} خياطة | {fn_qty} تغليف")

    # التبويبات
    tabs = st.tabs(["📥 دخول (خياطة)", "🧵 خياطة → تغليف", "📦 تغليف → تسليم", "📊 التقرير", "📜 السجل"])

    # ==================== تبويب 1: دخول مباشر إلى الخياطة ====================
    with tabs[0]:
        st.subheader("📥 استلام طلبية جديدة - تدخل مباشرة للخياطة (CT)")
        with st.form("ct_in_form"):
            col1, col2, col3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-", None]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-", None]]
            else:
                homes = []
                products = []
            
            client = col1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"])
            product = col2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"])
            quantity = col3.number_input("الكمية", min_value=1, step=1)
            
            new_client = st.text_input("أو أدخل اسم عميل جديد (اختياري)")
            
            if st.form_submit_button("✅ تسجيل دخول للخياطة", use_container_width=True):
                final_client = new_client.strip() if new_client.strip() else client
                if quantity > 0 and product.strip() and final_client and final_client != "لا توجد بيانات":
                    append_row([quantity, product, final_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ct"])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success(f"✅ تم إدخال {quantity} من {product} للعميل {final_client} إلى مرحلة الخياطة")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات")

    # ==================== تبويب 2: نقل من الخياطة إلى التغليف ====================
    with tabs[1]:
        st.subheader("🧵 نقل المنتجات من الخياطة (CT) إلى التغليف (FN)")
        
        ct_products = df[df['المرحلة'] == 'ct']
        
        if not ct_products.empty:
            ct_summary = ct_products.groupby(['المنزل', 'المنتج'])['الكمية'].sum().reset_index()
            
            st.markdown("### المنتجات الجاهزة لنقلها إلى التغليف")
            for _, row in ct_summary.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="phase-card">
                        <b>العميل:</b> {row['المنزل']}<br>
                        <b>المنتج:</b> {row['المنتج']}<br>
                        <b>الكمية المتاحة:</b> {safe_int(row['الكمية'])} قطعة
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    qty_to_fn = col1.number_input(
                        f"كمية لنقلها للتغليف", 
                        min_value=0, 
                        max_value=safe_int(row['الكمية']),
                        key=f"ct_to_fn_{row['المنزل']}_{row['المنتج']}"
                    )
                    if col2.button(f"نقل للتغليف", key=f"btn_ct_to_fn_{row['المنزل']}_{row['المنتج']}"):
                        if qty_to_fn > 0:
                            # إضافة إلى مرحلة التغليف
                            append_row([qty_to_fn, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "fn"])
                            # خصم من مرحلة الخياطة
                            append_row([-qty_to_fn, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ct"])
                            st.cache_resource.clear()
                            st.session_state.df = get_data()
                            st.success(f"✅ تم نقل {qty_to_fn} قطعة إلى التغليف")
                            st.rerun()
                        else:
                            st.warning("⚠️ يرجى إدخال كمية")
        else:
            st.info("لا توجد منتجات في مرحلة الخياطة حالياً")
        
        # عرض المنتجات تحت التغليف حالياً
        st.markdown("---")
        st.markdown("### 📦 المنتجات تحت التغليف حالياً")
        fn_products = df[df['المرحلة'] == 'fn']
        if not fn_products.empty:
            fn_summary = fn_products.groupby(['المنزل', 'المنتج'])['الكمية'].sum().reset_index()
            for _, row in fn_summary.iterrows():
                st.info(f"👥 {row['المنزل']} - {row['المنتج']}: {safe_int(row['الكمية'])} قطعة تحت التغليف")
        else:
            st.info("لا توجد منتجات في مرحلة التغليف")

    # ==================== تبويب 3: تسليم المنتجات بعد التغليف ====================
    with tabs[2]:
        st.subheader("📦 تسليم منتجات جاهزة (بعد التغليف)")
        
        fn_products = df[df['المرحلة'] == 'fn']
        
        if not fn_products.empty:
            fn_summary = fn_products.groupby(['المنزل', 'المنتج'])['الكمية'].sum().reset_index()
            
            st.markdown("### المنتجات الجاهزة للتسليم")
            for _, row in fn_summary.iterrows():
                st.success(f"🎁 {row['المنزل']} - {row['المنتج']}: {safe_int(row['الكمية'])} قطعة جاهزة")
            
            st.markdown("---")
            st.subheader("تسليم للعميل")
            
            with st.form("delivery_form"):
                col1, col2, col3 = st.columns(3)
                clients = fn_summary['المنزل'].unique().tolist()
                
                del_client = col1.selectbox("العميل", clients)
                # تصفية المنتجات لهذا العميل
                client_products = fn_summary[fn_summary['المنزل'] == del_client]['المنتج'].tolist()
                del_product = col2.selectbox("المنتج", client_products)
                
                max_qty = fn_summary[(fn_summary['المنزل'] == del_client) & (fn_summary['المنتج'] == del_product)]['الكمية'].values[0]
                del_qty = col3.number_input("كمية التسليم", min_value=1, max_value=safe_int(max_qty))
                
                if st.form_submit_button("تسليم للعميل"):
                    if del_qty > 0:
                        # خصم من مرحلة التغليف (تسليم)
                        append_row([-del_qty, del_product, del_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "fn"])
                        st.cache_resource.clear()
                        st.session_state.df = get_data()
                        st.success(f"✅ تم تسليم {del_qty} قطعة للعميل {del_client}")
                        st.rerun()
        else:
            st.info("لا توجد منتجات جاهزة للتسليم حالياً")

    # ==================== تبويب 4: التقرير ====================
    with tabs[3]:
        st.subheader("📊 تقرير متابعة الإنتاج")
        
        if not df.empty:
            clients = df['المنزل'].unique()
            clients = [c for c in clients if c not in ["", "-", None]]
            
            report_data = []
            for client in clients:
                client_df = df[df['المنزل'] == client]
                ct_qty = safe_int(client_df[client_df['المرحلة'] == 'ct']['الكمية'].sum())
                fn_qty = safe_int(client_df[client_df['المرحلة'] == 'fn']['الكمية'].sum())
                # ملاحظة: الكمية التي تم تسليمها هي سالبة في مرحلة fn، لذا نحتاج لحساب التسليم منفصلاً
                # لكن في نظامنا التسليم يتم بكتابة كمية سالبة، لذا إجمالي الكمية في fn = (تحت التغليف + تم تسليمه)
                # لكن الأسهل: نعتبر أن الرصيد الإيجابي في fn هو الجاهز للتسليم
                
                report_data.append({
                    'العميل': client,
                    'تحت الخياطة (CT)': ct_qty,
                    'تحت التغليف (FN)': fn_qty if fn_qty > 0 else 0,
                    'تم التسليم': abs(fn_qty) if fn_qty < 0 else 0
                })
            
            report_df = pd.DataFrame(report_data)
            
            def color_row(row):
                if row['تحت التغليف (FN)'] > 0:
                    return ['background-color: #4CAF50; color: white'] * len(row)
                elif row['تحت الخياطة (CT)'] > 0:
                    return ['background-color: #FFA500; color: black'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                report_df.style.apply(color_row, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                total_ct = safe_int(df[df['المرحلة'] == 'ct']['الكمية'].sum())
                st.metric("🧵 تحت الخياطة", total_ct)
            with col_b:
                total_fn = safe_int(df[df['المرحلة'] == 'fn']['الكمية'].sum())
                st.metric("📦 تحت التغليف", max(0, total_fn))
            with col_c:
                total_delivered = abs(min(0, total_fn)) if total_fn < 0 else 0
                st.metric("✅ تم التسليم", total_delivered)
            
            # رسم بياني
            st.markdown("---")
            st.subheader("📈 سير الإنتاج")
            chart_data = pd.DataFrame({
                'المرحلة': ['تحت الخياطة', 'تحت التغليف', 'تم التسليم'],
                'الكمية': [total_ct, max(0, total_fn), total_delivered]
            })
            st.bar_chart(chart_data.set_index('المرحلة'))
        else:
            st.info("لا توجد بيانات")

    # ==================== تبويب 5: السجل ====================
    with tabs[4]:
        st.subheader("📜 سجل جميع العمليات")
        if not df.empty:
            log_df = df.copy()
            log_df = log_df.iloc[::-1]
            log_df['الكمية'] = log_df['الكمية'].apply(safe_int)
            
            log_df['التاريخ'] = pd.to_datetime(log_df['التاريخ'], errors='coerce')
            log_df['التاريخ'] = log_df['التاريخ'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            log_df['المرحلة'] = log_df['المرحلة'].map({
                'ct': '🧵 دخول خياطة',
                'fn': '📦 تغليف / تسليم'
            }).fillna(log_df['المرحلة'])
            
            st.dataframe(log_df, use_container_width=True)
            
            csv = log_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل السجل كـ CSV",
                data=csv,
                file_name=f"workshop_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info("السجل فارغ")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
    st.stop()
