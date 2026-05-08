import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime
import plotly.express as px

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

def append_row(row):
    sheet = get_sheet()
    if sheet:
        sheet.append_row(row)

# 3. الواجهة
try:
    if "df" not in st.session_state:
        st.session_state.df = get_data()
    df = st.session_state.df

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: 
        st.title("🛡️ نظام الرقابة المطور")
        st.caption("نظام إدارة المخزون والمنازل")
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
            st.metric("🏠 عدد المنازل", df['المنزل'].nunique())
        with col3:
            st.metric("📦 عدد المنتجات", df['المنتج'].nunique())
        with col4:
            total_qty = df['الكمية'].sum()
            st.metric("📈 إجمالي الكميات", f"{int(total_qty)}")

    tabs = st.tabs(["🏠 استلام", "📤 إخراج", "🏢 المخزن", "💰 كشف حساب", "📜 History", "✅ إنجاز", "📊 تحليلات"])

    # --- TAB 1: استلام ---
    with tabs[0]:
        st.subheader("📦 استلام الإنتاج")
        if not df.empty:
            homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
            if homes:
                for home in homes:
                    with st.expander(f"🏠 منزل: {home}"):
                        home_data = df[df['المنزل'] == home]
                        for prod in home_data['المنتج'].unique():
                            p_data = home_data[home_data['المنتج'] == prod]
                            rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                            if rem > 0:
                                st.write(f"**{prod}** (المتبقي: {int(rem)})")
                                c1, c2 = st.columns([3, 1])
                                qty_in = c1.number_input(f"الكمية", min_value=0, key=f"in_{home}_{prod}")
                                if c2.button("تأكيد", key=f"btn_in_{home}_{prod}"):
                                    if qty_in > 0:
                                        append_row([qty_in, prod, home, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "st"])
                                        st.cache_resource.clear()
                                        st.session_state.df = get_data()
                                        st.success("✅ تمت العملية بنجاح")
                                        st.rerun()
                                    else:
                                        st.warning("⚠️ يرجى إدخال كمية صحيحة")
            else:
                st.info("لا توجد منازل مسجلة حالياً")
        else:
            st.info("لا توجد بيانات لعرضها")

    # --- TAB 2: إخراج ---
    with tabs[1]:
        st.subheader("📤 إخراج بضاعة جديدة")
        with st.form("out_form"):
            f1, f2, f3 = st.columns(3)
            
            if not df.empty:
                homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
                products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
            else:
                homes = []
                products = []

            o_h = f1.selectbox("اسم المنزل", options=homes if homes else ["لا توجد بيانات"])
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
                    st.success("✅ تم تسجيل العملية بنجاح")
                    st.rerun()
                else:
                    st.warning("⚠️ يرجى إدخال جميع البيانات بشكل صحيح")

    # --- TAB 3: المخزن ---
    with tabs[2]:
        st.subheader("🏢 رصيد الشركة")
        if not df.empty:
            s_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
            s_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
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
    with tabs[3]:
        st.subheader("💰 كشف حساب المنازل")
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
                'st': 'استلام',
                'ct': 'خروج كامل',
                'fn': 'خروج ناقص'
            })
            
            st.dataframe(pivot_table, use_container_width=True)
            
            # إضافة مجموع لكل منزل
            st.markdown("---")
            st.subheader("📊 ملخص المنازل")
            home_summary = df.groupby('المنزل')['الكمية'].sum().sort_values(ascending=False)
            for home, qty in home_summary.items():
                st.metric(home, f"{int(qty)} قطعة")
        else:
            st.info("لا توجد بيانات لعرضها")

    # --- TAB 5: السجل ---
    with tabs[4]:
        st.subheader("📜 سجل المعاملات (آخر 50) ")
        if not df.empty:
            history_df = df.iloc[::-1].head(50)
            # تنسيق التاريخ للعرض
            history_df['التاريخ'] = pd.to_datetime(history_df['التاريخ'], errors='coerce')
            history_df['التاريخ'] = history_df['التاريخ'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(history_df, use_container_width=True)
            
            # زر لتصدير البيانات
            csv = history_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل السجل كـ CSV",
                data=csv,
                file_name=f"history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.info("السجل فارغ حالياً.")

    # --- TAB 6: إنجاز ---
    with tabs[5]:
        st.subheader("✅ إنجاز المنازل")
        if not df.empty:
            summary = df.groupby("المنزل").agg(
                عدد_المنتجات=("المنتج", "nunique"),
                مجموع_الكمية=("الكمية", "sum"),
                عدد_المعاملات=("الكمية", "count")
            ).reset_index()
            
            # إضافة عمود الحالة
            def get_status(row):
                if row['مجموع_الكمية'] == 0:
                    return "⚠️ لم ينجز"
                elif row['مجموع_الكمية'] < 100:
                    return "🟡 قيد العمل"
                else:
                    return "✅ منجز"
            
            summary['الحالة'] = summary.apply(get_status, axis=1)
            
            # تنسيق الأعمدة
            summary['مجموع_الكمية'] = summary['مجموع_الكمية'].astype(int)
            
            # عرض الجدول مع تلوين الصفوف
            def highlight_status(row):
                if row['الحالة'] == '⚠️ لم ينجز':
                    return ['background-color: #ff4b4b20; color: #ff4b4b'] * len(row)
                elif row['الحالة'] == '🟡 قيد العمل':
                    return ['background-color: #ffa50020; color: #ffa500'] * len(row)
                return ['background-color: #4CAF5020; color: #4CAF50'] * len(row)
            
            st.dataframe(
                summary.style.apply(highlight_status, axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # رسوم بيانية للإنجاز
            st.markdown("---")
            fig = px.bar(summary, x='المنزل', y='مجموع_الكمية', title='إجمالي الكميات لكل منزل',
                        color='الحالة', color_discrete_map={
                            '✅ منجز': '#4CAF50',
                            '🟡 قيد العمل': '#FFA500',
                            '⚠️ لم ينجز': '#FF4444'
                        })
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات حالياً.")
    
    # --- TAB 7: تحليلات - جديد ---
    with tabs[6]:
        st.subheader("📊 تحليلات متقدمة")
        if not df.empty:
            col_ch1, col_ch2 = st.columns(2)
            
            with col_ch1:
                # أكثر المنتجات تداولاً
                top_products = df.groupby('المنتج')['الكمية'].sum().sort_values(ascending=False).head(10)
                fig1 = px.bar(top_products, x=top_products.values, y=top_products.index, 
                             orientation='h', title='أكثر 10 منتجات تداولاً')
                fig1.update_layout(height=400)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_ch2:
                # نشاط المنازل على مدار الوقت
                df_copy = df.copy()
                df_copy['التاريخ'] = pd.to_datetime(df_copy['التاريخ'], errors='coerce')
                daily_activity = df_copy.groupby(df_copy['التاريخ'].dt.date)['الكمية'].sum().reset_index()
                if not daily_activity.empty:
                    fig2 = px.line(daily_activity, x='التاريخ', y='الكمية', title='النشاط اليومي')
                    fig2.update_layout(height=400)
                    st.plotly_chart(fig2, use_container_width=True)
            
            # توزيع المعاملات حسب النوع
            st.markdown("---")
            col_ch3, col_ch4 = st.columns(2)
            
            with col_ch3:
                type_dist = df['الحالة'].value_counts()
                fig3 = px.pie(values=type_dist.values, names=type_dist.index, title='توزيع المعاملات')
                fig3.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig3, use_container_width=True)
            
            with col_ch4:
                # إحصائيات إضافية
                st.info(f"""
                **📈 إحصائيات عامة:**
                - أول معاملة: {df['التاريخ'].min() if not df['التاريخ'].isna().all() else 'N/A'}
                - آخر معاملة: {df['التاريخ'].max() if not df['التاريخ'].isna().all() else 'N/A'}
                - متوسط الكمية لكل معاملة: {df['الكمية'].mean():.1f}
                - أعلى كمية في معاملة: {int(df['الكمية'].max())}
                """)
        else:
            st.info("لا توجد بيانات كافية للتحليل")

except Exception as e:
    st.error(f"حدث خطأ غير متوقع: {e}")
    st.exception(e)
