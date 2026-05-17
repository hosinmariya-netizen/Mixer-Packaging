import streamlit as st
from gsheetsdb import connect
import pandas as pd

# إعداد الاتصال بـ Google Sheets (تأكد من أن الرابط يحتوي على صلاحية الوصول)
# استبدل هذا الرابط برابط الـ Spreadsheet الخاص بك إذا لزم الأمر
sheet_url = st.secrets["public_gsheets_url"]

# دالة لجلب بيانات الحسابات من الورقة المحددة
@st.cache_data(ttl=600)  # تحديث البيانات كل 10 دقائق
def load_accounts_data():
    # هنا نقوم بطلب ورقة "كلمات سر وحسابات" محددة
    # ملحوظة: تأكد من صياغة الاستعلام لجلب الورقة الصحيحة، أو استخدام pandas لقراءتها عبر الرابط المخفي للورقة
    # الطريقة الأسهل مع المقارنة المباشرة:
    query = f'SELECT * FROM "{sheet_url}"'
    # إذا كنت تستخدم مكتبة st.connection الحديثة في Streamlit (وهي الأسهل):
    # conn = st.connection("gsheets", type=GSheetsConnection)
    # df = conn.read(worksheet="كلمات سر وحسابات")
    
    # سنفترض هنا استخدام الرابط المباشر لورقة "كلمات سر وحسابات" عبر الباندا لضمان الدقة:
    # نقوم بتحويل الرابط العادي لرابط تصدير CSV مع اسم الورقة
    csv_url = sheet_url.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=كلمات%20سر%20وحسابات")
    csv_url = csv_url.replace("/edit#gid=", "/gviz/tq?tqx=out:csv&sheet=كلمات%20سر%20وحسابات")
    df = pd.read_csv(csv_url)
    return df

# تحميل جدول الحسابات
try:
    df_accounts = load_accounts_data()
except Exception as e:
    st.error("حدث خطأ أثناء الاتصال بجدول الحسابات، تأكد من اسم الورقة والرابط.")
    df_accounts = pd.DataFrame()

# إدارة حالة تسجيل الدخول باستخدام Session State في Streamlit
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول - نظام إدارة الورشة")
    
    username_input = st.text_input("اسم الحساب:")
    password_input = st.text_input("كلمة السر:", type="password")
    
    if st.button("دخول"):
        if not df_accounts.empty:
            # التحقق من وجود الحساب وكلمة السر في الأعمدة "الحساب" و "كلمة السر"
            # نقوم بتحويل المدخلات لنصوص والتأكد من مطابقتها تماماً لما في الصورة
            match = df_accounts[(df_accounts['الحساب'].astype(str) == username_input) & 
                                (df_accounts['كلمة السر'].astype(str) == str(password_input))]
            
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success(f"مرحباً بك يا {username_input}، تم تسجيل الدخول بنجاح!")
                st.rerun() # إعادة تحميل الصفحة لعرض النظام
            else:
                st.error("اسم الحساب أو كلمة السر غير صحيحة.")
        else:
            st.error("تعذر التحقق من الحسابات حالياً.")

# --- محتوى الموقع الرئيسي (يظهر فقط بعد تسجيل الدخول بنجاح) ---
else:
    # شريط علوي يظهر اسم المستخدم وزر تسجيل الخروج
    st.sidebar.write(f"👤 المستخدم الحالي: **{st.session_state.username}**")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("🏗️ لوحة تحكم ورقة السلع والعمل")
    st.write("مرحباً بك في النظام. يمكنك الآن تصفح ورقة 'السلع' وإدارتها.")
    
    # --- كود جلب ورقة "السلع" القديم الخاص بك يوضع هنا ---
    # مثال:
    # csv_goods_url = sheet_url.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=السلع")
    # df_goods = pd.read_csv(csv_goods_url)
    # st.dataframe(df_goods)
    
