import streamlit as st
from config import COLORS, BACKGROUND_IMAGE, MESSAGES

def apply_custom_styles():
    """تطبيق التنسيقات والأنماط المخصصة"""
    st.markdown(f"""
    <style>
    /* الخلفية والألوان الأساسية */
    .stApp {{
        background-color: {COLORS['primary']};
        color: white;
        direction: rtl;
        background-image: url("{BACKGROUND_IMAGE}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* طبقة شفافة على الخلفية */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: {COLORS['overlay']};
        z-index: 0;
    }}
    
    /* الأزرار */
    .stButton > button {{
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        transition: all 0.3s ease;
        border: 2px solid {COLORS['primary']};
        background-color: #1f77b4;
        color: white;
    }}
    
    .stButton > button:hover {{
        background-color: #1560a0;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }}
    
    /* حقول الإدخال */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {{
        border-radius: 8px;
        padding: 10px;
        background-color: #1e1e1e;
        color: white;
        border: 2px solid #404040;
        font-size: 16px;
    }}
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: #1f77b4;
        box-shadow: 0 0 10px rgba(31, 119, 180, 0.5);
    }}
    
    /* تبويبات */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        padding: 0 20px;
        background-color: #1e1e1e;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        border: 2px solid #404040;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #1f77b4;
        color: white;
        border-color: #1f77b4;
    }}
    
    /* الرسائل */
    .stSuccess {{
        padding: 15px;
        border-radius: 8px;
        background-color: #0d3b0d;
        border-left: 4px solid #21ba45;
    }}
    
    .stError {{
        padding: 15px;
        border-radius: 8px;
        background-color: #3d0d0d;
        border-left: 4px solid #ff4b4b;
    }}
    
    .stWarning {{
        padding: 15px;
        border-radius: 8px;
        background-color: #3d2b0d;
        border-left: 4px solid #ff9800;
    }}
    
    .stInfo {{
        padding: 15px;
        border-radius: 8px;
        background-color: #0d2b3d;
        border-left: 4px solid #1f77b4;
    }}
    
    /* الجداول */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
    }}
    
    .dataframe th {{
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 12px;
        text-align: right;
    }}
    
    .dataframe td {{
        padding: 10px;
        border-bottom: 1px solid #404040;
        color: white;
        text-align: right;
    }}
    
    .dataframe tr:hover {{
        background-color: #2a2a2a;
    }}
    
    /* العناوين */
    h1, h2, h3, h4, h5, h6 {{
        color: white;
        text-align: right;
        font-weight: bold;
    }}
    
    /* النصوص */
    p, span, label {{
        color: white;
        text-align: right;
    }}
    
    /* البطاقات والمربعات */
    .stMetric {{
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #404040;
    }}
    
    .stMetric > div:first-child {{
        color: #999;
        text-align: right;
    }}
    
    .stMetric > div:last-child {{
        color: #1f77b4;
        font-size: 28px;
        font-weight: bold;
        text-align: right;
    }}
    
    /* الإطارات */
    .stExpander {{
        background-color: #1e1e1e;
        border: 2px solid #404040;
        border-radius: 8px;
    }}
    
    .stExpander > div:first-child {{
        color: white;
        font-weight: bold;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #1e1e1e;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: #1f77b4;
        border-radius: 5px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: #1560a0;
    }}
    
    /* النماذج */
    .stForm {{
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #404040;
    }}
    
    /* الراديو والـ Checkbox */
    .stRadio > div {{
        flex-direction: row-reverse;
    }}
    
    .stCheckbox > div {{
        flex-direction: row-reverse;
    }}
    
    /* الأيقونات والرموز */
    .stMarkdown {{
        text-align: right;
    }}
    
    /* الشريط الجانبي */
    [data-testid="stSidebar"] {{
        background-color: #0e1117;
        border-right: 2px solid #404040;
    }}
    
    /* الكاميرات والأدوات */
    .stCameraInput {{
        text-align: center;
    }}
    
    /* الأعمدة */
    [data-testid="column"] {{
        padding: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

def show_success_message(message: str = MESSAGES['success']):
    """عرض رسالة نجاح"""
    st.success(f"✅ {message}")

def show_error_message(message: str = MESSAGES['error']):
    """عرض رسالة خطأ"""
    st.error(f"❌ {message}")

def show_warning_message(message: str = MESSAGES['warning']):
    """عرض رسالة تنبيه"""
    st.warning(f"⚠️ {message}")

def show_info_message(message: str = MESSAGES['empty']):
    """عرض رسالة معلومات"""
    st.info(f"ℹ️ {message}")

def create_metric_card(label: str, value: str, color: str = "#1f77b4"):
    """إنشاء بطاقة مقياس مخصصة"""
    st.metric(label, value)

def create_section_header(title: str, icon: str = "📋"):
    """إنشاء رأس قسم مخصص"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1f77b4 0%, #1560a0 100%);
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 5px solid #1f77b4;
    ">
        <h2 style="margin: 0; color: white; text-align: right;">
            {icon} {title}
        </h2>
    </div>
    """, unsafe_allow_html=True)

def create_horizontal_line():
    """إنشاء خط أفقي"""
    st.markdown("---")

def create_footer():
    """إنشاء تذييل احترافي"""
    st.markdown("""
    <div style="
        text-align: center;
        padding: 20px;
        margin-top: 40px;
        border-top: 2px solid #404040;
        color: #999;
    ">
        <p>🛡️ نظام الرقابة الذكية - Bébé Sympa</p>
        <p>© 2026 جميع الحقوق محفوظة</p>
        <p>تم التطوير بواسطة: <strong>hosinmariya-netizen</strong></p>
    </div>
    """, unsafe_allow_html=True)

def highlight_row(row):
    """تلوين الصفوف في الجداول"""
    return ['background-color: #2a2a2a;' if i % 2 == 0 else '' for i in range(len(row))]

def create_loading_spinner():
    """عرض مؤشر التحميل"""
    with st.spinner('⏳ جاري التحميل...'):
        pass

def create_sidebar_menu():
    """إنشاء قائمة في الشريط الجانبي"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("📊 الإحصائيات")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("المنتجات", "0")
        with col2:
            st.metric("الكمية", "0")
        
        st.markdown("---")
        st.subheader("🔧 الإعدادات")
        
        if st.button("🔄 تحديث البيانات"):
            st.rerun()
        
        if st.button("❌ مسح التخزين المؤقت"):
            st.cache_resource.clear()
            st.rerun()

def apply_responsive_design():
    """تطبيق تصميم متجاوب"""
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """, unsafe_allow_html=True)
