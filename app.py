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
        direction: rtl;
    }
    .stButton>button { 
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }
    .stAlert {
        direction: rtl;
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
        expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
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

# 3. الواجهة الرئيسية
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والعملاء - Bébé Sympa")
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

    # التبويبات الرئيسية
    tabs = st.tabs(["📥 دخول", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 السجل", "✅ إنجاز"])

    # ==================== تبويب 1: دخول ====================
    with tabs[0]:
        st.subheader("📥 تسجيل دخول بضاعة")
        with st.form("in_form"):
            col1, col2, col3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
            else:
                homes = []
                products = []
            
            in_home = col1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"])
            in_product = col2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"])
            in_qty = col3.number_input("الكمية", min_value=1)
            
            # إضافة عميل جديد
            new_client = st.text_input("أو أدخل اسم عميل جديد (اختياري)")
            
            if st.form_submit_button("✅ تسجيل الدخول", use_container_width=True):
                final_client = new_client.strip() if new_client.strip() else in_home
                if in_qty > 0 and in_product.strip() and final_client and final_client != "لا توجد بيانات":
                    append_row([in_qty, in_product, final_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success(f"✅ تم تسجيل الدخول بنجاح للعميل: {final_client}")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # ==================== تبويب 2: إخراج ====================
    with tabs[1]:
        st.subheader("📤 تسجيل خروج بضاعة")
        with st.form("out_form"):
            col1, col2, col3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
            else:
                homes = []
                products = []
            
            out_home = col1.selectbox("اسم العميل", options=homes if homes else ["لا توجد بيانات"])
            out_product = col2.selectbox("اسم المنتج", options=products if products else ["لا توجد بيانات"])
            out_qty = col3.number_input("الكمية", min_value=1)
            out_type = st.radio("نوع الخروج", ["كامل (ct)", "ناقص (fn)"], horizontal=True)
            out_value = "ct" if "كامل" in out_type else "fn"
            
            if st.form_submit_button("✅ تسجيل الخروج", use_container_width=True):
                if out_qty > 0 and out_product.strip() and out_home.strip() and out_home != "لا توجد بيانات":
                    append_row([out_qty, out_product, out_home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), out_value])
                    st.cache_resource.clear()
                    st.session_state.df = get_data()
                    st.success(f"✅ تم تسجيل الخروج بنجاح للعميل: {out_home}")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # ==================== تبويب 3: المخزن ====================
    with tabs[2]:
        st.subheader("🏢 رصيد المخزن")
        if not df.empty:
            # حساب الداخل
            stock_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            # حساب الخارج (ct + fn)
            stock_out_ct = df[df['الحالة'] == 'ct'].groupby('المنتج')['الكمية'].sum()
            stock_out_fn = df[df['الحالة'] == 'fn'].groupby('المنتج')['الكمية'].sum()
            stock_out = stock_out_ct.add(stock_out_fn, fill_value=0)
            
            # الرصيد
            balance = (stock_in - stock_out).fillna(stock_in).reset_index()
            balance.columns = ['المنتج', 'الرصيد']
            balance['الرصيد'] = balance['الرصيد'].astype(int)
            
            total_balance = balance['الرصيد'].sum()
            st.metric("📦 إجمالي الرصيد", f"{int(total_balance)} قطعة")
            
            st.markdown("---")
            for _, row in balance.iterrows():
                if row['الرصيد'] > 0:
                    st.info(f"✅ {row['المنتج']}: {row['الرصيد']} قطعة")
                elif row['الرصيد'] < 0:
                    st.error(f"⚠️ {row['المنتج']}: عجز {abs(row['الرصيد'])} قطعة")
        else:
            st.info("لا توجد بيانات")

    # ==================== تبويب 4: كشف حساب ====================
    with tabs[3]:
        st.subheader("💰 كشف حساب العملاء")
        if not df.empty:
            # إنشاء جدول محوري
            pivot = df.pivot_table(
                index='المنزل',
                columns='الحالة',
                values='الكمية',
                aggfunc='sum',
                fill_value=0
            )
            
            # إعادة تسمية الأعمدة
            pivot = pivot.rename(columns={
                'st': '📥 دخول',
                'ct': '📤 خروج كامل',
                'fn': '📤 خروج ناقص'
            })
            
            # إضافة عمود الرصيد
            pivot['💰 الرصيد'] = pivot.get('📥 دخول', 0) - (pivot.get('📤 خروج كامل', 0) + pivot.get('📤 خروج ناقص', 0))
            pivot = pivot.astype(int)
            
            st.dataframe(pivot, use_container_width=True)
        else:
            st.info("لا توجد بيانات")

    # ==================== تبويب 5: السجل ====================
    with tabs[4]:
        st.subheader("📜 سجل جميع المعاملات")
        if not df.empty:
            # تجهيز البيانات للعرض
            log_df = df.copy()
            log_df = log_df.iloc[::-1]  # عكس الترتيب (الأحدث أولاً)
            log_df['الكمية'] = log_df['الكمية'].astype(int)
            
            # تنسيق التاريخ
            log_df['التاريخ'] = pd.to_datetime(log_df['التاريخ'], errors='coerce')
            log_df['التاريخ'] = log_df['التاريخ'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # ترجمة الحالة
            log_df['نوع العملية'] = log_df['الحالة'].map({
                'st': '📥 دخول',
                'ct': '📤 خروج كامل',
                'fn': '📤 خروج ناقص'
            }).fillna(log_df['الحالة'])
            
            # اختيار الأعمدة للعرض
            display_cols = ['المنزل', 'المنتج', 'الكمية', 'نوع العملية', 'التاريخ']
            st.dataframe(log_df[display_cols], use_container_width=True)
            
            # إحصائيات سريعة
            col_a, col_b = st.columns(2)
            with col_a:
                in_count = len(log_df[log_df['الحالة'] == 'st'])
                st.info(f"📥 عدد عمليات الدخول: {in_count}")
            with col_b:
                out_count = len(log_df[log_df['الحالة'].isin(['ct', 'fn'])])
                st.error(f"📤 عدد عمليات الخروج: {out_count}")
            
            # زر تحميل
            csv = log_df[display_cols].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل السجل كـ CSV",
                data=csv,
                file_name=f"history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info("السجل فارغ")

    # ==================== تبويب 6: إنجاز ====================
    with tabs[5]:
        st.subheader("✅ إنجاز العملاء")
        if not df.empty:
            # حساب إجمالي لكل عميل
            clients = df['المنزل'].unique()
            clients = [c for c in clients if c not in ["", "-"]]
            
            result_data = []
            for client in clients:
                client_df = df[df['المنزل'] == client]
                total_in = client_df[client_df['الحالة'] == 'st']['الكمية'].sum()
                total_out = client_df[client_df['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                balance = total_in - total_out
                products_count = client_df['المنتج'].nunique()
                
                result_data.append({
                    'العميل': client,
                    'عدد المنتجات': int(products_count),
                    'مجموع الدخول': int(total_in),
                    'مجموع الخروج': int(total_out),
                    'الرصيد': int(balance)
                })
            
            result_df = pd.DataFrame(result_data)
            
            # تلوين الصفوف
            def color_row(row):
                if row['الرصيد'] == 0:
                    return ['background-color: #4CAF50; color: white'] * len(row)
                elif row['الرصيد'] < 0:
                    return ['background-color: #ff4b4b; color: white'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                result_df.style.apply(color_row, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # إحصائيات
            st.markdown("---")
            completed = len(result_df[result_df['الرصيد'] == 0])
            negative = len(result_df[result_df['الرصيد'] < 0])
            positive = len(result_df[result_df['الرصيد'] > 0])
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.success(f"✅ منجز (رصيد 0): {completed}")
            with col_b:
                st.error(f"⚠️ عليهم دين: {negative}")
            with col_c:
                st.info(f"📦 لديهم رصيد: {positive}")
        else:
            st.info("لا توجد بيانات")

except Exception as e:
    st.error(f"حدث خطأ: {e}")
