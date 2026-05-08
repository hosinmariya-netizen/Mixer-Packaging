import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# إعداد الصفحة
st.set_page_config(page_title="Bébé Sympa - جرد الكميات", layout="wide")

# الاتصال
conn = st.connection("gsheets", type=GSheetsConnection)

# جلب البيانات
df = conn.read(ttl=0)
df.columns = df.columns.str.strip()

# تحويل عمود الكمية إلى أرقام (لضمان صحة الحساب)
if 'الكمية' in df.columns:
    df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)

st.title("📊 جرد كميات الإنتاج الفعلي")

tab1, tab2 = st.tabs(["📈 إجمالي الكميات", "📋 التفاصيل"])

with tab1:
    if 'المنتج' in df.columns and 'الحالة' in df.columns and 'الكمية' in df.columns:
        # هنا السحر: سنقوم بجمع (Sum) عمود الكمية وليس عد الأسطر
        inventory_sum = df.groupby(['المنتج', 'الحالة'])['الكمية'].sum().unstack(fill_value=0)
        
        # التأكد من الأعمدة
        if 'ct' not in inventory_sum.columns: inventory_sum['ct'] = 0
        if 'fn' not in inventory_sum.columns: inventory_sum['fn'] = 0
        
        inventory_sum = inventory_sum[['ct', 'fn']]
        inventory_sum.columns = ['إجمالي كمية الخياطة (ct)', 'إجمالي كمية التغليف (fn)']
        
        # إضافة المجموع الكلي لكل منتج
        inventory_sum['المجموع الكلي'] = inventory_sum['إجمالي كمية الخياطة (ct)'] + inventory_sum['إجمالي كمية التغليف (fn)']
        
        # عرض المربعات الكبيرة بالمجموع الحسابي
        c1, c2, c3 = st.columns(3)
        c1.metric("🧵 مجموع قطع الخياطة", int(inventory_sum['إجمالي كمية الخياطة (ct)'].sum()))
        c2.metric("🎁 مجموع قطع التغليف", int(inventory_sum['إجمالي كمية التغليف (fn)'].sum()))
        c3.metric("📦 العدد الإجمالي للمصنع", int(inventory_sum['المجموع الكلي'].sum()))
        
        st.divider()
        st.table(inventory_sum)
    else:
        st.error("تنبيه: يجب أن يحتوي الجدول على عمود اسمه 'الكمية' ويحتوي على أرقام.")

with tab2:
    st.dataframe(df, use_container_width=True)
    
