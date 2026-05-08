import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - الرقابة الذكية", layout="wide", page_icon="🛡️")

# رابط اللوجو
logo_path = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# التنسيق
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; direction: rtl; }
    .stButton>button { border-radius: 10px; }
    .warning-text { color: #ff4b4b; font-weight: bold; padding: 10px; border: 1px solid #ff4b4b; border-radius: 5px; }
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

    # الهيدر وزر التحديث
    col_t, col_ref = st.columns([4, 1])
    with col_t: st.title("🛡️ نظام الرقابة والاستلام")
    with col_ref: 
        if st.button("🔄 تحديث البيانات"): st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏠 استلام من المنازل", "🏢 المخزن النهائي", "💰 كشف الحساب"])

    # --- التبويب الأول: الرقابة الصارمة على الاستلام ---
    with tab1:
        st.subheader("📦 إدارة المستلمات من المنازل")
        homes = [h for h in df['المنزل'].unique() if h != "-"]
        
        for home in homes:
            with st.expander(f"🏠 منزل: {home}"):
                home_data = df[df['المنزل'] == home]
                prods = home_data['المنتج'].unique()
                
                for prod in prods:
                    p_data = home_data[home_data['المنتج'] == prod]
                    # حساب الخارج (ct + fn) والمستلم سابقاً (st)
                    total_out = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum()
                    already_in = p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    max_allowed = total_out - already_in
                    
                    if max_allowed > 0:
                        st.markdown(f"--- \n **المنتج:** {prod}")
                        c1, c2, c3 = st.columns([2, 2, 1])
                        
                        with c1:
                            input_qty = st.number_input(f"الكمية المستلمة (الحد الأقصى {int(max_allowed)})", 
                                                       min_value=0, step=1, key=f"qty_{home}_{prod}")
                        
                        # منطق التحذير والتجاهل
                        is_over = input_qty > max_allowed
                        ignore_warning = False
                        
                        if is_over:
                            st.markdown(f'<p class="warning-text">⚠️ تحذير: الكمية ({int(input_qty)}) أكبر من الصادرة ({int(max_allowed)})!</p>', unsafe_allow_html=True)
                            ignore_warning = st.checkbox("تجاهل التحذير وتأكيد الكمية الزائدة", key=f"ign_{home}_{prod}")
                        
                        with c2:
                            # لا يظهر الزر أو لا يعمل إلا إذا كانت الكمية صحيحة أو تم اختيار التجاهل
                            btn_disabled = is_over and not ignore_warning
                            if st.button(f"✓ تأكيد الاستلام", key=f"btn_{home}_{prod}", disabled=btn_disabled):
                                if input_qty > 0:
                                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                                    new_row = pd.DataFrame([{
                                        "المنزل": home, "المنتج": prod, "الكمية": input_qty, 
                                        "الحالة": "st", "التاريخ": now
                                    }])
                                    update_data(pd.concat([df, new_row], ignore_index=True))
                                    st.success("تم تسجيل الاستلام بنجاح!")
                    else:
                        st.caption(f"✅ {prod}: تم استلام كامل الكمية الصادرة.")

    # --- التبويب الثاني: المخزن النهائي ---
    with tab2:
        st.subheader("🏢 رصيد الشركة الحالي")
        stock_final = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum().reset_index()
        stock_final.columns = ['اسم المنتج', 'المخزن (st)']
        st.table(stock_final)

    # --- التبويب الثالث: تتبع الحركات ---
    with tab3:
        st.subheader("💰 ملخص العمليات المنجزة للدفع")
        payment_summary = df[df['الحالة'].isin(['ct', 'fn'])].groupby(['المنزل', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
        st.dataframe(payment_summary, use_container_width=True)

except Exception as e:
    st.error(f"خطأ في البيانات: {e}")
        
