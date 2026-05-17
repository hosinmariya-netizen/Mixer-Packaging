import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة والعناوين
st.set_page_config(page_title="نظام إدارة الورشة - Bébé Sympa", page_icon="🏗️", layout="centered")

# تأكد من أن الرابط الخاص بك مضاف في ملف .streamlit/secrets.toml باسم public_gsheets_url
# أو يمكنك استبدال st.secrets["public_gsheets_url"] برابط جدول البيانات الخاص بك مباشرة بين علامتي تنصيص.
# ضع رابط ملف الـ Google Sheets الخاص بك مباشرة بين علامتي التنصيص هنا:
SHEET_URL = "https://docs.google.com/spreadsheets/d/ضع_هنا_الرقم_الخاص_بملفك/edit?usp=sharing"
# 2. دالة جلب البيانات من Google Sheets وتحويلها إلى لوحة بيانات (Pandas DataFrame)
@st.cache_data(ttl=300)  # تحديث البيانات تلقائيًا كل 5 دقائق
def get_sheet_data(sheet_name):
    # تحويل الرابط العادي لرابط تصدير CSV متوافق مع اسم الورقة المطلوبة بدقة
    base_url = SHEET_URL.split("/edit")[0]
    csv_url = f"{base_url}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(csv_url)

# 3. إدارة حالة تسجيل الدخول (Session State) للحفاظ على الجلسة مفتوحة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- أولاً: شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #4F8BF9;'>🔐 تسجيل الدخول إلى النظام</h2>", unsafe_allow_html=True)
    st.write("برجاء إدخال اسم الحساب وكلمة السر المعتمدة في ورقة الحسابات:")
    
    # حقول الإدخال
    username_input = st.text_input("اسم الحساب (المستخدم):", placeholder="مثال: حسين")
    password_input = st.text_input("كلمة السر:", type="password", placeholder="••••")
    
    if st.button("تسجيل الدخول", use_container_width=True):
        if username_input.strip() == "" or password_input.strip() == "":
            st.warning("الرجاء ملء جميع الحقول أولاً.")
        else:
            with st.spinner("جاري التحقق من بيانات الحساب..."):
                try:
                    # جلب بيانات ورقة "كلمات سر وحسابات"
                    df_accounts = get_sheet_data("كلمات%20سر%20وحسابات")
                    
                    # تنظيف البيانات من أي مسافات زائدة وتحويلها لنصوص للمطابقة الصحيحة
                    df_accounts['الحساب'] = df_accounts['الحساب'].astype(str).str.strip()
                    df_accounts['كلمة السر'] = df_accounts['كلمة السر'].astype(str).str.strip()
                    
                    # التحقق من مطابقة المدخلات مع أسطر الجدول
                    match = df_accounts[
                        (df_accounts['الحساب'] == username_input.strip()) & 
                        (df_accounts['كلمة السر'] == password_input.strip())
                    ]
                    
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = username_input.strip()
                        st.success(f"مرحباً بك يا {username_input}! تم الدخول بنجاح.")
                        st.rerun()  # إعادة تحميل التطبيق لفتح النظام للـمستخدم
                    else:
                        st.error("❌ اسم الحساب أو كلمة السر غير صحيحة، يرجى المحاولة مرة أخرى.")
                except Exception as e:
                    st.error("⚠️ تعذر الاتصال بجدول البيانات للتأكد من الحساب.")
                    st.info("تأكد من أن خيار المشاركة في Google Sheets مضبوط على 'أي شخص لديه الرابط يمكنه العرض'.")

# --- ثانياً: شاشة النظام الرئيسية (تظهر بعد تسجيل الدخول بنجاح فقط) ---
else:
    # القائمة الجانبية (Sidebar) لإظهار معلومات المستخدم وزر الخروج
    st.sidebar.markdown(f"### 👤 الحساب الحالي:\n **{st.session_state.username}**")
    if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
        
    # محتوى لوحة التحكم لإدارة الورشة
    st.markdown(f"<h2>🏗️ لوحة تحكم ورشة Bébé Sympa</h2>", unsafe_allow_html=True)
    st.write(f"أهلاً بك يا **{st.session_state.username}**، تم تحميل بيانات الورشة بنجاح.")
    
    # جلب وعرض بيانات ورقة "السلع"
    st.markdown("### 📦 جدول السلع والمخزون الحالي")
    with st.spinner("جاري تحديث جدول السلع من Google Sheets..."):
        try:
            df_goods = get_sheet_data("السلع")
            
            # عرض جدول السلع بشكل منسق وجذاب
            st.dataframe(df_goods, use_container_width=True)
            
            # يمكنك إضافة أزرار إحصائية بسيطة هنا بناءً على السلع المتاحة لديك
            st.info(f"إجمالي عدد المواد والسلع المسجلة حالياً: {len(df_goods)} صنف.")
            
        except Exception as e:
            st.error("حدث خطأ أثناء تحميل ورقة السلع. تأكد من أن اسم الورقة هو 'السلع' بالضبط.")
    
