import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging

# إعداد Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ إعدادات الصفحة ============
st.set_page_config(
    page_title="Bébé Sympa - نظام الرقابة الذكية",
    layout="wide",
    page_icon="🛡️"
)

# ============ التنسيقات ============
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: white;
        direction: rtl;
    }
    
    .stButton > button {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        background-color: #1f77b4;
        color: white;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #1560a0;
        transform: translateY(-2px);
    }
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        background-color: #1e1e1e;
        color: white;
        border: 2px solid #404040;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e1e;
        border-radius: 8px;
        color: white;
        font-weight: bold;
    }
    
    .stMetric {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #404040;
    }
    
    .dataframe {
        border-radius: 8px;
    }
    
    h1, h2, h3 {
        color: white;
        text-align: right;
    }
    
    .success-text {
        color: #21ba45;
        font-weight: bold;
    }
    
    .error-text {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============ فئة لإدارة Google Sheets ============
class SheetsManager:
    def __init__(self):
        self.sheet = None
        self.authenticate()
    
    def authenticate(self):
        """الاتصال بـ Google Sheets"""
        try:
            creds_dict = st.secrets["gcp_service_account"]
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso")
            self.sheet = spreadsheet.sheet1
            logger.info("✅ تم الاتصال بـ Google Sheets")
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال: {e}")
            st.error(f"❌ خطأ في الاتصال بـ Google Sheets: {e}")
    
    def get_data(self) -> pd.DataFrame:
        """الحصول على البيانات"""
        try:
            if not self.sheet:
                return pd.DataFrame()
            
            data = self.sheet.get_all_records()
            df = pd.DataFrame(data)
            
            # تأكد من وجود الأعمدة الضرورية
            required_cols = ["الكمية", "المنتج", "المنزل", "التاريخ", "الحالة"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            
            df = df[required_cols]
            df['الكمية'] = pd.to_numeric(df['الكمية'], errors='coerce').fillna(0)
            return df
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة البيانات: {e}")
            st.error(f"❌ خطأ في قراءة البيانات: {e}")
            return pd.DataFrame()
    
    def add_row(self, row_data):
        """إضافة صف جديد"""
        try:
            if not self.sheet:
                st.error("❌ الجدول غير متصل")
                return False
            
            self.sheet.append_row(row_data)
            logger.info(f"✅ تم إضافة صف: {row_data}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الصف: {e}")
            st.error(f"❌ خطأ في إضافة البيانات: {e}")
            return False

# ============ التهيئة ============
@st.cache_resource
def get_sheets_manager():
    return SheetsManager()

manager = get_sheets_manager()

# ============ الواجهة الرئيسية ============
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.title("🛡️ نظام الرقابة الذكية - Bébé Sympa")

with col_refresh:
    if st.button("🔄 تحديث"):
        st.cache_resource.clear()
        st.rerun()

st.divider()

# ============ الألسنة ============
tabs = st.tabs(["📥 استلام", "📤 إخراج", "📊 المخزن", "📈 كشف حساب", "📜 السجل", "✅ الإنجاز"])

# ============ التبويب 1: الاستلام ============
with tabs[0]:
    st.subheader("📥 استلام الإنتاج")
    
    if "df" not in st.session_state:
        st.session_state.df = manager.get_data()
    
    df = st.session_state.df
    
    if not df.empty:
        homes = [h for h in df['المنزل'].unique() if h not in ["-", ""]]
        
        for home in homes:
            with st.expander(f"🏠 منزل: {home}", expanded=False):
                home_data = df[df['المنزل'] == home]
                
                for prod in home_data['المنتج'].unique():
                    p_data = home_data[home_data['المنتج'] == prod]
                    remaining = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                    
                    if remaining > 0:
                        st.write(f"**{prod}** - المتبقي: **{int(remaining)}** قطعة")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            qty = st.number_input(
                                "الكمية",
                                min_value=0,
                                key=f"in_{home}_{prod}",
                                label_visibility="collapsed"
                            )
                        with col2:
                            if st.button("✅ تأكيد", key=f"btn_in_{home}_{prod}"):
                                if qty > 0:
                                    row = [qty, prod, home, datetime.now().strftime("%Y-%m-%d %H:%M"), "st"]
                                    if manager.add_row(row):
                                        st.session_state.df = manager.get_data()
                                        st.success("✅ تمت العملية بنجاح!")
                                        st.rerun()
                                else:
                                    st.warning("⚠️ يرجى إدخال كمية صحيحة")
    else:
        st.info("📭 لا توجد بيانات حالياً")

# ============ التبويب 2: الإخراج ============
with tabs[1]:
    st.subheader("📤 إخراج بضاعة جديدة")
    
    with st.form("out_form"):
        col1, col2, col3 = st.columns(3)
        
        homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
        products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
        
        with col1:
            out_home = st.selectbox("اسم المنزل", options=homes if homes else [""])
        with col2:
            out_product = st.selectbox("اسم المنتج", options=products if products else [""])
        with col3:
            out_qty = st.number_input("الكمية", min_value=1)
        
        out_status = st.radio("الحالة", ["خياطة (ct)", "انتهاء (fn)"], horizontal=True)
        status_map = {"خياطة (ct)": "ct", "انتهاء (fn)": "fn"}
        
        if st.form_submit_button("🔔 تسجيل الخروج"):
            if out_qty > 0 and out_product and out_home:
                row = [out_qty, out_product, out_home, datetime.now().strftime("%Y-%m-%d %H:%M"), status_map[out_status]]
                if manager.add_row(row):
                    st.session_state.df = manager.get_data()
                    st.success("✅ تم تسجيل العملية بنجاح!")
                    st.rerun()
            else:
                st.warning("⚠️ يرجى إدخال جميع البيانات")

# ============ التبويب 3: المخزن ============
with tabs[2]:
    st.subheader("📊 رصيد الشركة")
    
    if not df.empty:
        stock_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        stock_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        stock = stock_in.subtract(stock_out, fill_value=0).reset_index()
        stock.columns = ['المنتج', 'الكمية']
        
        total = stock['الكمية'].sum()
        st.metric("إجمالي الرصيد", f"{int(total)} قطعة")
        
        st.dataframe(stock, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التبويب 4: كشف الحساب ============
with tabs[3]:
    st.subheader("📈 كشف حساب المنازل")
    
    if not df.empty:
        summary = df.pivot_table(
            index='المنزل',
            columns='الحالة',
            values='الكمية',
            aggfunc='sum',
            fill_value=0
        )
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التبويب 5: السجل ============
with tabs[4]:
    st.subheader("📜 سجل المعاملات")
    
    if not df.empty:
        history = df.iloc[::-1].head(50)
        st.dataframe(history, use_container_width=True)
    else:
        st.info("📭 السجل فارغ")

# ============ التبويب 6: الإنجاز ============
with tabs[5]:
    st.subheader("✅ إنجاز المنازل")
    
    if not df.empty:
        completed = df.groupby("المنزل").agg(
            عدد_المنتجات=("المنتج", "nunique"),
            مجموع_الكمية=("الكمية", "sum")
        ).reset_index()
        
        st.dataframe(completed, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التذييل ============
st.divider()
st.markdown("""
<div style="text-align: center; padding: 20px; color: #999;">
    <p>🛡️ نظام الرقابة الذكية - Bébé Sympa</p>
    <p>© 2026 جميع الحقوق محفوظة</p>
    <p>تم التطوير بواسطة: <strong>hosinmariya-netizen</strong></p>
</div>
""", unsafe_allow_html=True)
            
