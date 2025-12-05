"""
ماژول تنظیمات و پیکربندی MasterGrader
این ماژول تمام پارامترهای قابل تنظیم سیستم را مدیریت می‌کند.
"""

import os
from pathlib import Path


class Config:
    """کلاس مدیریت تنظیمات سیستم"""
    
    # ==============================
    # مسیرها (Paths)
    # ==============================
    ROOT_DIR = r"F:\assignment_94318_submissions_by_user"  # مسیر اصلی پوشه دانشجویان
    OUTPUT_DIR = r"./Smart_Organized_Submissions"  # مسیر خروجی فایل‌های مرتب شده
    LOGS_DIR = r"./logs"  # مسیر ذخیره لاگ‌ها
    TEMPLATE_CODE_PATH = None  # مسیر فایل کد قالب (اختیاری) - برای حذف کدهای آماده استاد
    
    # ==============================
    # پارامترهای تصحیح (Grading Parameters)
    # ==============================
    NUM_QUESTIONS = 6  # تعداد سوالات تمرین
    SIMILARITY_THRESHOLD = 95.0  # آستانه شباهت برای تشخیص تقلب (درصد)
    MIN_TOKEN_COUNT = 50  # حداقل تعداد توکن برای بررسی تقلب (جلوگیری از False Positive)
    
    # ==============================
    # فرمت‌های فایل (File Formats)
    # ==============================
    ACCEPTED_EXTENSIONS = ['.c', '.cpp', '.h']  # پسوندهای قابل قبول
    ZIP_EXTENSIONS = ['.zip', '.rar', '.7z']  # پسوندهای فشرده
    
    # ==============================
    # تنظیمات استخراج (Extraction Settings)
    # ==============================
    MAX_EXTRACTION_DEPTH = 10  # حداکثر عمق استخراج بازگشتی (جلوگیری از حلقه بی‌نهایت)
    IGNORE_PATTERNS = ['__MACOSX', '.DS_Store', 'Thumbs.db', '.git']  # الگوهای نادیده گرفته شده
    
    # ==============================
    # تنظیمات تشخیص تقلب (Plagiarism Detection)
    # ==============================
    TOKENIZATION_ENABLED = True  # فعال/غیرفعال کردن توکن‌سازی
    NORMALIZE_WHITESPACE = True  # نرمال‌سازی فاصله‌های خالی
    REMOVE_COMMENTS = True  # حذف کامنت‌ها
    REMOVE_INCLUDES = True  # حذف #include ها
    IGNORE_VARIABLES = False  # در صورت True، نام متغیرها در مقایسه نادیده گرفته می‌شود
    
    # ==============================
    # تنظیمات گزارش‌دهی (Reporting)
    # ==============================
    REPORT_ENCODING = 'utf-8-sig'  # انکودینگ فایل CSV (برای اکسل)
    CONSOLE_OUTPUT_ENABLED = True  # نمایش خروجی در کنسول
    DETAILED_LOGGING = True  # لاگ‌گیری تفصیلی
    
    # ==============================
    # کلمات کلیدی C (C Keywords)
    # ==============================
    C_KEYWORDS = {
        'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
        'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
        'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
        'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
    }
    
    # ==============================
    # عملگرها و نمادهای C (C Operators & Symbols)
    # ==============================
    C_OPERATORS = {
        '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
        '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '++', '--',
        '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
        '->', '.', '?', ':', ',', ';', '(', ')', '[', ']', '{', '}'
    }
    
    @classmethod
    def initialize_directories(cls):
        """ایجاد پوشه‌های مورد نیاز در صورت عدم وجود"""
        directories = [cls.OUTPUT_DIR, cls.LOGS_DIR]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
            # ایجاد پوشه‌های سوالات
            if directory == cls.OUTPUT_DIR:
                for q_num in range(1, cls.NUM_QUESTIONS + 1):
                    q_dir = Path(directory) / f"Q{q_num}"
                    q_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[+] Output folders are ready: {cls.OUTPUT_DIR}")
    
    @classmethod
    def validate_config(cls):
        """اعتبارسنجی تنظیمات"""
        errors = []
        
        if not os.path.exists(cls.ROOT_DIR):
            errors.append(f"Input path does not exist: {cls.ROOT_DIR}")
        
        if cls.NUM_QUESTIONS < 1:
            errors.append("Number of questions must be at least 1")
        
        if not (0 <= cls.SIMILARITY_THRESHOLD <= 100):
            errors.append("Similarity threshold must be between 0 and 100")
        
        if cls.MIN_TOKEN_COUNT < 1:
            errors.append("Minimum token count must be positive")
        
        return errors
    
    @classmethod
    def get_log_file_path(cls):
        """مسیر فایل لاگ"""
        return os.path.join(cls.LOGS_DIR, "logs.txt")
    
    @classmethod
    def get_report_file_path(cls):
        """مسیر فایل گزارش تقلب"""
        return os.path.join(cls.OUTPUT_DIR, "Plagiarism_Report.csv")
    
    @classmethod
    def get_html_reports_dir(cls):
        """مسیر پوشه گزارش‌های HTML"""
        return os.path.join(cls.OUTPUT_DIR, "HTML_Reports")

