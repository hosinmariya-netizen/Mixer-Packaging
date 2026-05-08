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
        font-weight: bold;
    }
    .stButton>button:hover { 
        background-color: #45a049;
    }
    .warning-text { color: #ff4b4b; font-weight: bold; }
    .success-text { color: #4CAF50; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بجوجل شيت مع تحسين الكاش
@st.cache_resource
def get_sheet():
    try:        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

@st.cache_data(ttl=60)  # تحديث البيانات كل 60 ثانية كحد أقصى
def get_data():
    sheet = get_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            expected_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
            # إضافة الأعمدة الناقصة
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            # تحويل الكمية إلى رقم
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة البيانات: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_clients(df):
    """جلب قائمة العملاء من البيانات الموجودة في الذاكرة"""
    if not df.empty:
        unique_clients = [h for h in df['المنزل'].unique() if pd.notna(h) and str(h).strip() not in ["", "-"]]
        return sorted(unique_clients)
    return []

def append_row(row):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"خطأ في الحفظ: {e}")
            return False
    return False

# 3. الواجهة الرئيسيةtry:
    # تحميل البيانات مرة واحدة وتحديثها عند الحاجة
    if "df" not in st.session_state or st.session_state.get("refresh_data", False):
        st.session_state.df = get_data()
        st.session_state.refresh_data = False
    
    df = st.session_state.df
    clients_list = get_clients(df)

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والعملاء - Bébé Sympa")
    with col_ref:
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.cache_data.clear()
            st.session_state.refresh_data = True
            st.rerun()

    # إحصائيات سريعة
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 إجمالي المعاملات", f"{len(df):,}")
        with col2:
            st.metric("🏠 عدد العملاء", f"{df['المنزل'].nunique():,}")
        with col3:
            st.metric("📦 أنواع المنتجات", f"{df['المنتج'].nunique():,}")
        with col4:
            total_qty = df['الكمية'].sum()
            st.metric("📈 إجمالي الكميات", f"{int(total_qty):,}")

    tabs = st.tabs(["👥 العملاء", "📥 دخول", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز"])

    # --- TAB 0: إدارة العملاء ---
    with tabs[0]:
        st.subheader("👥 إدارة العملاء")
        st.markdown("### 🏠 العملاء المسجلون في النظام")
        if clients_list:
            st.success(f"✅ عدد العملاء النشطين: **{len(clients_list)}**")
            # عرض العملاء في أعمدة لتنظيم العرض
            cols = st.columns(3)
            for idx, client in enumerate(clients_list):
                cols[idx % 3].info(f"👤 {client}")
        else:
            st.info("💡 لا يوجد عملاء في النظام بعد. ابدأ بتسجيل عملية دخول أو خروج لإضافة عميل جديد.")
        
        st.markdown("---")
        st.caption("💡 ملاحظة: يتم إضافة العملاء تلقائياً عند تسجيل أول معاملة لهم")
    # --- TAB 1: دخول ---
    with tabs[1]:
        st.subheader("📥 تسجيل دخول بضاعة جديدة")
        with st.form("in_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            
            homes = [""] + clients_list if clients_list else ["لا توجد بيانات"]
            products = [""] + [p for p in df['المنتج'].unique() if pd.notna(p) and str(p).strip()] if not df.empty else ["لا توجد بيانات"]

            in_home = f1.selectbox("🏠 اسم العميل", options=homes, key="in_home")
            in_product = f2.selectbox("📦 اسم المنتج", options=products, key="in_product")
            in_qty = f3.number_input("🔢 الكمية", min_value=1, step=1, key="in_qty")
            
            new_client = st.text_input("✨ أو أدخل اسم عميل جديد (اختياري)", placeholder="اكتب الاسم هنا...")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
            with col_btn2:
                submitted = st.form_submit_button("✅ تأكيد تسجيل الدخول", use_container_width=True, type="primary")
            
            if submitted:
                final_client = new_client.strip() if new_client.strip() else in_home
                if in_qty > 0 and in_product and in_product != "لا توجد بيانات" and final_client and final_client != "لا توجد بيانات":
                    if append_row([in_qty, in_product, final_client, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"]):
                        st.cache_data.clear()
                        st.session_state.refresh_data = True
                        st.success(f"✅ تم تسجيل الدخول بنجاح للعميل: {final_client}")
                        st.rerun()
                else:
                    st.warning("⚠️ يرجى التأكد من إدخال جميع البيانات بشكل صحيح")

    # --- TAB 2: إخراج ---
    with tabs[2]:
        st.subheader("📤 تسجيل خروج بضاعة")
        with st.form("out_form", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            
            homes = [""] + clients_list if clients_list else ["لا توجد بيانات"]
            products = [""] + [p for p in df['المنتج'].unique() if pd.notna(p) and str(p).strip()] if not df.empty else ["لا توجد بيانات"]

            o_h = f1.selectbox("🏠 اسم العميل", options=homes)
            o_p = f2.selectbox("📦 اسم المنتج", options=products)
            o_q = f3.number_input("🔢 الكمية", min_value=1, step=1)
            o_s = st.radio("📋 نوع الخروج", ["✅ كامل (ct)", "❌ ناقص (fn)"], horizontal=True)
            o_s_value = "ct" if "كامل" in o_s else "fn"
            
            col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
            with col_btn2:
                submitted = st.form_submit_button("✅ تأكيد تسجيل الخروج", use_container_width=True, type="primary")
                        if submitted:
                if o_q > 0 and o_p and o_p != "لا توجد بيانات" and o_h and o_h != "لا توجد بيانات":
                    if append_row([o_q, o_p, o_h, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), o_s_value]):
                        st.cache_data.clear()
                        st.session_state.refresh_data = True
                        st.success(f"✅ تم تسجيل الخروج بنجاح (النوع: {o_s_value})")
                        st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 3: المخزن ---
    with tabs[3]:
        st.subheader("🏢 رصيد الشركة (المخزن المركزي)")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out_ct = df[df['الحالة'] == 'ct'].groupby('المنتج')['الكمية'].sum()
            s_out_fn = df[df['الحالة'] == 'fn'].groupby('المنتج')['الكمية'].sum()
            s_out = s_out_ct.add(s_out_fn, fill_value=0)
            stock = s_in.subtract(s_out, fill_value=0).reset_index()
            stock.columns = ['المنتج', 'الكمية']
            stock['الكمية'] = stock['الكمية'].astype(int)
            total_stock = stock['الكمية'].sum()
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("📦 إجمالي الرصيد في المخزن", f"{int(total_stock):,} قطعة")
            
            if not stock.empty:
                # عرض المنتجات المتوفرة فقط
                available_stock = stock[stock['الكمية'] > 0].sort_values('الكمية', ascending=False)
                if not available_stock.empty:
                    st.dataframe(available_stock, use_container_width=True, hide_index=True,
                                column_config={"المنتج": "المنتج", "الكمية": st.column_config.NumberColumn("الكمية المتوفرة", format="%d")})
                else:
                    st.warning("⚠️ المخزن فارغ حالياً")
            else:
                st.info("لا توجد بيانات للمخزن")
        else:
            st.info("📭 لا توجد بيانات لعرضها")

    # --- TAB 4: كشف الحساب ---
    with tabs[4]:
        st.subheader("💰 كشف حساب العملاء")
        if not df.empty:
            pivot_table = df.pivot_table(
                index='المنزل', 
                columns='الحالة', 
                values='الكمية', 
                aggfunc='sum', 
                fill_value=0            )
            
            # إعادة تسمية الأعمدة للتوضيح
            rename_cols = {'st': '📥 دخول', 'ct': '📤 خروج كامل', 'fn': '📤 خروج ناقص'}
            existing_cols = {k: v for k, v in rename_cols.items() if k in pivot_table.columns}
            pivot_table = pivot_table.rename(columns=existing_cols)
            
            # تحويل الأرقام إلى أعداد صحيحة
            for col in pivot_table.columns:
                pivot_table[col] = pivot_table[col].astype(int)
            
            st.dataframe(pivot_table, use_container_width=True, help="جدول يوضح حركات كل عميل")
        else:
            st.info("لا توجد بيانات لعرضها")

    # --- TAB 5: History مع ألوان ---
    with tabs[5]:
        st.subheader("📜 سجل المعاملات (آخر 50 عملية)")
        if not df.empty:
            history_df = df.iloc[::-1].head(50).copy()
            
            # تحويل الكمية إلى عدد صحيح
            history_df['الكمية'] = history_df['الكمية'].astype(int)
            
            # تنسيق التاريخ للعرض
            history_df['التاريخ'] = pd.to_datetime(history_df['التاريخ'], errors='coerce')
            history_df['التاريخ'] = history_df['التاريخ'].dt.strftime('%Y-%m-%d %H:%M')
            
            # إضافة عمود نوع العملية للعرض
            history_df['نوع العملية'] = history_df['الحالة'].map({
                'st': '📥 دخول',
                'ct': '📤 خروج كامل',
                'fn': '📤 خروج ناقص'
            }).fillna(history_df['الحالة'])
            
            # إنشاء DataFrame للعرض
            display_df = history_df[['المنزل', 'المنتج', 'الكمية', 'نوع العملية', 'التاريخ']].copy()
            
            # تلوين الصفوف حسب نوع العملية
            def color_rows(row):
                if 'دخول' in str(row['نوع العملية']):
                    return ['background-color: rgba(76, 175, 80, 0.2); color: #4CAF50; font-weight: bold'] * len(row)
                else:
                    return ['background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold'] * len(row)
            
            # عرض الجدول بالألوان
            styled_df = display_df.style.apply(color_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # إحصائيات سريعة            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                total_in = len(history_df[history_df['الحالة'] == 'st'])
                st.info(f"📥 عمليات الدخول: {total_in}")
            with col_stat2:
                total_out = len(history_df[history_df['الحالة'].isin(['ct', 'fn'])])
                st.error(f"📤 عمليات الخروج: {total_out}")
            
            # زر لتصدير البيانات
            csv = history_df[['المنزل', 'المنتج', 'الكمية', 'الحالة', 'التاريخ']].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل السجل كملف CSV",
                data=csv,
                file_name=f"history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info("📭 السجل فارغ حالياً.")

    # --- TAB 6: إنجاز ---
    with tabs[6]:
        st.subheader("✅ إنجاز العملاء وتصفية الأرصدة")
        if not df.empty:
            # ✅ الحساب الصحيح باستخدام groupby.agg
            summary = df.groupby('المنزل').agg(
                عدد_المنتجات=('المنتج', 'nunique'),
                مجموع_الدخول=('الكمية', lambda x: x[df.loc[x.index, 'الحالة'] == 'st'].sum()),
                مجموع_الخروج=('الكمية', lambda x: x[df.loc[x.index, 'الحالة'].isin(['ct', 'fn'])].sum())
            ).reset_index()
            
            # حساب الرصيد
            summary['الرصيد'] = (summary['مجموع_الدخول'] - summary['مجموع_الخروج']).astype(int)
            
            # إعادة تسمية الأعمدة للعرض
            summary.columns = ['العميل', 'عدد المنتجات', 'مجموع الدخول', 'مجموع الخروج', 'الرصيد']
            
            # تلوين الصفوف حسب حالة الرصيد
            def highlight_balance(row):
                if row['الرصيد'] == 0:
                    return ['background-color: rgba(76, 175, 80, 0.3); color: #4CAF50; font-weight: bold'] * len(row)
                elif row['الرصيد'] < 0:
                    return ['background-color: rgba(255, 75, 75, 0.3); color: #ff4b4b; font-weight: bold'] * len(row)
                return [''] * len(row)

            st.dataframe(
                summary.style.apply(highlight_balance, axis=1),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "العميل": "🏠 العميل",                    "عدد المنتجات": st.column_config.NumberColumn("📦 المنتجات", format="%d"),
                    "مجموع الدخول": st.column_config.NumberColumn("📥 الدخول", format="%d"),
                    "مجموع الخروج": st.column_config.NumberColumn("📤 الخروج", format="%d"),
                    "الرصيد": st.column_config.NumberColumn("⚖️ الرصيد", format="%d")
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
                st.success(f"✅ منجزون (رصيد 0): {completed_clients}")
            with col_stat2:
                st.error(f"⚠️ عليهم رصيد (سالب): {negative_clients}")
            with col_stat3:
                st.info(f"📦 لديهم رصيد (موجب): {positive_clients}")
            
        else:
            st.info("📭 لا توجد بيانات حالياً.")

except Exception as e:
    st.error(f"❌ حدث خطأ غير متوقع: {e}")
    with st.expander("🔍 عرض تفاصيل الخطأ للمطور"):
        st.exception(e)
