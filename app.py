import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa Pro", layout="wide", page_icon="🏠")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# تنسيق الواجهة (Dark Mode)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0e1117; color: white; direction: rtl; }}
    [data-testid="stMetric"] {{ background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #00a4e4; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
    .stTabs [data-baseweb="tab"] {{ background-color: #1e293b; border-radius: 10px; padding: 10px 20px; color: white; }}
    .stExpander {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; margin-bottom: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# ---Header مع زر التحديث ---
col_t, col_ref = st.columns([4, 1])
with col_t:
    st.title("🏠 إدارة إنتاج Bébé Sympa")
with col_ref:
    if st.button("🔄 تحديث فوري"):
        st.cache_data.clear()
        st.rerun()

try:
    # جلب البيانات وتنظيفها
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()
    
    # تحويل الكمية لرقم لضمان الحساب الصحيح
    if 'الكمية' in df.columns:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    tab1, tab2 = st.tabs(["📊 جرد الكميات حسب المنازل", "📋 سجل الحركات الكامل"])

    with tab1:
        st.subheader("📦 تفاصيل المنتجات (اضغط لرؤية المنازل)")
        
        if all(col in df.columns for col in ['المنتج', 'الحالة', 'الكمية']):
            # جلب قائمة المنتجات الفريدة
            products = df['المنتج'].unique()
            
            for product in products:
                # فلترة البيانات لكل منتج
                p_data = df[df['المنتج'] == product]
                q_ct = p_data[p_data['الحالة'].str.lower() == 'ct']['الكمية'].sum()
                q_fn = p_data[p_data['الحالة'].str.lower() == 'fn']['الكمية'].sum()
                
                # عنوان القائمة المنسدلة (Expander)
                expander_title = f"🔹 {product} | خياطة: {int(q_ct)} | تغليف: {int(q_fn)} | الإجمالي: {int(q_ct + q_fn)}"
                
                with st.expander(expander_title):
                    col_ct, col_fn = st.columns(2)
                    
                    with col_ct:
                        st.markdown("#### 🧵 في الخياطة (المنازل)")
                        ct_list = p_data[p_data['الحالة'].str.lower() == 'ct']
                        if not ct_list.empty:
                            # عرض عمود "المنزل" والكمية
                            target_col = 'المنزل' if 'المنزل' in df.columns else df.columns[0]
                            st.table(ct_list[[target_col, 'الكمية']])
                        else:
                            st.caption("لا توجد كميات في الخياطة")
                            
                    with col_fn:
                        st.markdown("#### 🎁 في التغليف (المنازل)")
                        fn_list = p_data[p_data['الحالة'].str.lower() == 'fn']
                        if not fn_list.empty:
                            target_col = 'المنزل' if 'المنزل' in df.columns else df.columns[0]
                            st.table(fn_list[[target_col, 'الكمية']])
                        else:
                            st.caption("لا توجد كميات في التغليف")
        else:
            st.error("تأكد من وجود الأعمدة التالية في الإكسل: المنتج، الحالة، الكمية، المنزل")

    with tab2:
        search = st.text_input("🔍 بحث في السجل التاريخي...")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
        st.dataframe(display_df, use_container_width=True)

except Exception as e:
    st.error(f"حدث خطأ في قراءة البيانات: {e}")
                        
