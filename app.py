import streamlit as st
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Mixer Packaging", page_icon="📦", layout="wide")

# 1. التحقق من الأسرار (Secrets) لتأمين الموقع
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# سنقوم بقراءة كلمة المرور من الـ Secrets الخاصة بـ Streamlit
# إذا لم تكن الأسرار مهيأة بعد، سنضع كلمة مرور افتراضية للمعاينة المحلية فقط
try:
    correct_password = st.secrets["auth"]["password"]
except:
    correct_password = "admin" # كلمة مرور مؤقتة للمحلي

st.sidebar.title("🔑 تسجيل الدخول")
password_input = st.sidebar.text_input("أدخل كلمة المرور:", type="password")

if password_input == correct_password:
    st.session_state.authenticated = True
    st.sidebar.success("تم التحقق بنجاح ✅")
else:
    if password_input:
        st.sidebar.error("كلمة المرور غير صحيحة ❌")

# 2. عرض التطبيق بعد تسجيل الدخول الناجح
if st.session_state.authenticated:
    st.title("📦 نظام إدارة التعبئة والمخزن (Mixer-Packaging)")
    
    # تقسيم الواجهة إلى علامات تبويب (Tabs) بناءً على جداولك المرفقة
    tab1, tab2 = st.tabs(["📋 جدول المنازل والحسابات", "🔢 مراجع الـ FN"])
    
    with tab1:
        st.header("إدارة بيانات المنازل")
        
        # قائمة الأسماء المأخوذة من ملفك
        names_list = [
            "بباز عيسى", "قمغار محمد", "قبايلي خضير", "نعلوفي عيسى", 
            "لالوة محمد", "بيايا توفيق", "أداود يحيى", "أداود عبد الرحمان",
            "أداود عمر", "بضليس فارس", "بضليس يوسف", "كيوكيو محمد",
            "سيوسيو نور الدين", "حجاج رستم", "باباحني يوسف", "باباحني خضير"
        ]
        
        col1, col2 = st.columns(2)
        with col1:
            selected_name = st.selectbox("اختر اسم المنزل / الزبون:", names_list)
            store_place = st.text_input("المخزن:", placeholder="أدخل اسم المخزن")
            delivery_no = st.text_input("رقم التوصيل (No Livrai):")
            
        with col2:
            input_qty = st.number_input("الكمية المدخلة (إدخال):", min_value=0, step=1)
            output_qty = st.number_input("الكمية المخرجة (إخراج):", min_value=0, step=1)
            current_date = st.date_input("التاريخ:", datetime.now())
            history_notes = st.text_area("السجل (History):", placeholder="ملاحظات السجل...")

        if st.button("💾 حفظ وتحديث البيانات"):
            st.success(f"تمت محاكاة تسجيل البيانات بنجاح لـ: {selected_name}")
            # هنا مستقبلاً يمكنك ربط هذا الزر بحفظ حقيقي داخل Google Sheets أو قاعدة بيانات
            
    with tab2:
        st.header("مراجع الـ FN والـ CT")
        # توليد جدول مراجع من Bv1 إلى Bv9 تلقائياً بناءً على ورقتك الأولى
        references = [f"Bv{i}" for i in range(1, 10)]
        fn_data = pd.DataFrame({
            "Référence FN": references,
            "CT": [""] * len(references) # حقول فارغة للتعبئة
        })
        
        # عرض الجدول بشكل تفاعلي يسمح للمستخدم بتعديله داخل الموقع
        edited_df = st.data_editor(fn_data, num_rows="dynamic", use_container_width=True)
        
        if st.button("📊 حفظ التعديلات على المراجع"):
            st.success("تم تحديث جدول المراجع تفاعلياً!")

else:
    st.info("🔒 الرجاء إدخال كلمة المرور في الشريط الجانبي للوصول إلى لوحة التحكم والبيانات.")
    
