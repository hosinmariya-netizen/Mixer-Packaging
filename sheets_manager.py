import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional
import logging
from datetime import datetime

# إعداد Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsManager:
    """فئة لإدارة Google Sheets بكفاءة واحترافية"""
    
    def __init__(self, sheet_url: str, scopes: List[str]):
        """
        تهيئة مدير Google Sheets
        
        Args:
            sheet_url: رابط جدول Google Sheets
            scopes: نطاقات الوصول
        """
        self.sheet_url = sheet_url
        self.scopes = scopes
        self.client = None
        self.sheet = None
        self.authenticate()
    
    def authenticate(self) -> bool:
        """التحقق من الهوية والاتصال بـ Google Sheets"""
        try:
            creds_dict = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(
                creds_dict, 
                scopes=self.scopes
            )
            self.client = gspread.authorize(creds)
            spreadsheet = self.client.open_by_url(self.sheet_url)
            self.sheet = spreadsheet.sheet1
            logger.info("✅ تم الاتصال بـ Google Sheets بنجاح")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال: {e}")
            st.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
            return False
    
    def get_all_data(self) -> pd.DataFrame:
        """الحصول على جميع البيانات من الجدول"""
        try:
            if not self.sheet:
                logger.warning("⚠️ الجدول غير متصل")
                return pd.DataFrame()
            
            data = self.sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty:
                logger.info("📭 الجدول فارغ")
            else:
                logger.info(f"✅ تم قراءة {len(df)} صف من البيانات")
            
            return df
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة البيانات: {e}")
            st.error(f"خطأ في قراءة البيانات: {e}")
            return pd.DataFrame()
    
    def add_row(self, row_data: List) -> bool:
        """إضافة صف جديد إلى الجدول"""
        try:
            if not self.sheet:
                logger.warning("⚠️ الجدول غير متصل")
                return False
            
            self.sheet.append_row(row_data)
            logger.info(f"✅ تم إضافة صف جديد: {row_data}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الصف: {e}")
            st.error(f"خطأ في إضافة البيانات: {e}")
            return False
    
    def update_row(self, row_index: int, row_data: List) -> bool:
        """تحديث صف موجود"""
        try:
            if not self.sheet:
                logger.warning("⚠️ الجدول غير متصل")
                return False
            
            self.sheet.delete_rows(row_index)
            self.sheet.insert_row(row_data, row_index)
            logger.info(f"✅ تم تحديث الصف {row_index}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الصف: {e}")
            st.error(f"خطأ في تحديث البيانات: {e}")
            return False
    
    def delete_row(self, row_index: int) -> bool:
        """حذف صف من الجدول"""
        try:
            if not self.sheet:
                logger.warning("⚠️ الجدول غير متصل")
                return False
            
            self.sheet.delete_rows(row_index)
            logger.info(f"✅ تم حذف الصف {row_index}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حذف الصف: {e}")
            st.error(f"خطأ في حذف البيانات: {e}")
            return False
    
    def get_row_count(self) -> int:
        """الحصول على عدد الصفوف"""
        try:
            if not self.sheet:
                return 0
            return len(self.sheet.get_all_records())
        except Exception as e:
            logger.error(f"❌ خطأ في عد الصفوف: {e}")
            return 0
    
    def clear_sheet(self) -> bool:
        """مسح جميع البيانات من الجدول"""
        try:
            if not self.sheet:
                logger.warning("⚠️ الجدول غير متصل")
                return False
            
            self.sheet.clear()
            logger.info("✅ تم مسح الجدول")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في مسح الجدول: {e}")
            return False

@st.cache_resource
def get_sheets_manager(sheet_url: str, scopes: List[str]) -> Optional[SheetsManager]:
    """الحصول على instance من SheetsManager مع التخزين المؤقت"""
    try:
        return SheetsManager(sheet_url, scopes)
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء SheetsManager: {e}")
        return None
