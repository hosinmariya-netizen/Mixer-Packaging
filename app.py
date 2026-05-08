import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - نظام الاستلام", layout="wide", page_icon="✅")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .stButton>button { border-radius: 10px; width: 100%; }
    .status-box { padding: 10px; border-radius: 5px; margin: 5px 0; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

def update_data(df):
    conn.update(data=df)
    st.cache_data.clear()
    st.rerun()

try:
    # جلب البيانات
    df = conn.read(ttl=0)
    df.columns = df.columns.str.strip()
    if 'الكمية' in df.columns:
        df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

    # الهيدر
    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("✅ نظام الاستلام والمدفوعات")
    with col_ref: 
        if st.button("🔄 تحديث"): st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏠 المنازل (تسليم)", "🏢 مخزن الشركة", "💰 حسابات نهاية الشهر"])

    # --- التبويب الأول: المنازل والاستلام ---
    with tab1:
        st.subheader("📦 سلع قيد العمل عند المنازل")
        # حساب الباقي الفعلي عند كل منزل (الخارج - المستلم)
        homes = df['المنزل'].unique()
        for home in homes:
            if home == "-": continue
            with st.expander(f"🏠 منزل: {home}"):
                home_data = df[df['المنزل'] == home]
                # عرض السلع التي لم تُستلم بالكامل بعد
                prods = home_data['المنتج'].unique()
                for prod in prods:
                    p_data = home_data[home_data['المنتج'] == prod]
                    # الكمية التي خرجت (ct + fn)
                    out_ct = p_data[p_data['الحالة'] == 'ct']['الكمية'].sum()
                    out_fn = p_data[p_data['الحالة'] == 'fn']['الكمية'].sum()
                    # الكمية التي عادت للمخزن (st)
                    in_st = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    
                    remaining = (out_ct + out_fn) - in_st
                    
                    if remaining > 0:
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"🔹 **{prod}** (الباقي بالخارج: {int(remaining)})")
                        with c2:
                            amount_to_receive = st.number_input(f"الكمية المستلمة من {prod}", min_value=1, max_value=int(remaining), key=f"in_{home}_{prod}")
                        with c3:
                            if st.button(f"✓ استلام", key=f"btn_{home}_{prod}"):
                                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                new_row = pd.DataFrame([{
                                    "المنزل": home, "المنتج": prod, "الكمية": amount_to_receive, 
                                    "الحالة": "st", "التاريخ": now
                                }])
                                updated_df = pd.concat([df, new_row], ignore_index=True)
                                update_data(updated_df)
                                st.success(f"تم استلام {amount_to_receive} قطعة!")

    # --- التبويب الثاني: المخزن النهائي ---
    with tab2:
        st.subheader("🏢 السلع الجاهزة في مخزن الشركة")
        stock_final = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum().reset_index()
        stock_final.columns = ['اسم المنتج', 'الكمية الجاهزة']
        st.table(stock_final)

    # --- التبويب الثالث: تتبع الحركات والمدفوعات ---
    with tab3:
        st.subheader("💳 كشف حساب العمليات المنجزة")
        # فلترة العمليات التي تمت (ct و fn) لحساب الأجر
        payment_df = df[df['الحالة'].isin(['ct', 'fn'])].copy()
        if not payment_df.empty:
            summary = payment_df.groupby(['المنزل', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
            st.write("📊 مجموع ما أنجزه كل منزل هذا الشهر:")
            st.dataframe(summary, use_container_width=True)
            
            st.divider()
            st.write("📝 سجل الحركات التاريخي للدفع:")
            st.dataframe(payment_df[['التاريخ', 'المنزل', 'المنتج', 'الحالة', 'الكمية']], use_container_width=True)

except Exception as e:
    st.error(f"تأكد من أعمدة الإكسل (المنزل، المنتج، الكمية، الحالة): {e}")
    
