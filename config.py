import os
from dotenv import load_dotenv

load_dotenv()

# ============ إعدادات Streamlit ============
PAGE_TITLE = "Bébé Sympa - نظام الرقابة الذكية"
PAGE_ICON = "shield"
LAYOUT = "wide"

# ============ إعدادات Google Sheets ============
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZUGpM6RBYDiLfX1Z5qKH5C6E2pfaRHF6dCDWmGXTso"
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# ============ أسماء الأعمدة ============
COLUMNS = {
    "quantity": "الكمية",
    "product": "المنتج",
    "home": "المنزل",
    "date": "التاريخ",
    "status": "الحالة"
}

REQUIRED_COLUMNS = list(COLUMNS.values())

# ============ حالات العمليات ============
STATUS = {
    "sent": "st",
    "cutting": "ct",
    "finished": "fn",
    "collected": "cl"
}

# ============ الألوان ============
COLORS = {
    "primary": "#0e1117",
    "overlay": "rgba(14, 17, 23, 0.92)",
    "success": "#21ba45",
    "error": "#ff4b4b",
    "warning": "#ff9800"
}

# ============ الصور ============
BACKGROUND_IMAGE = "https://raw.githubusercontent.com/hosinmariya-netizen/Mixer-Packaging/main/images%20(5)%20(5).jpeg"

# ============ إعدادات التطبيق ============
CACHE_TTL = 300  # 5 دقائق
MAX_HISTORY_ROWS = 50
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# ============ الرسائل ============
MESSAGES = {
    "success": "✅ تمت العملية بنجاح",
    "error": "❌ حدث خطأ",
    "warning": "⚠️ تنبيه",
    "empty": "📭 لا توجد بيانات حالياً",
    "loading": "⏳ جاري التحميل..."
}
