"""
ماژول تنظیمات و پیکربندی MasterGrader
این ماژول تمام پارامترهای قابل تنظیم سیستم را مدیریت می‌کند.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class SensitivityConfig:
    """
    کلاس تنظیمات حساسیت پیشرفته برای تشخیص تقلب.
    
    این کلاس امکان کنترل دقیق و گرانولار بر روی نحوه تشخیص تقلب را فراهم می‌کند.
    استاد می‌تواند برای هر عنصر کد به صورت جداگانه تصمیم بگیرد که آیا نادیده گرفته شود یا خیر.
    """
    # تنظیمات شناسه‌ها (Identifiers)
    ignore_variable_names: bool = False  # نادیده گرفتن نام متغیرها
    ignore_function_names: bool = False  # نادیده گرفتن نام توابع
    ignore_type_names: bool = False  # نادیده گرفتن نام انواع (struct, typedef, etc.)
    
    # تنظیمات مقادیر (Literals)
    ignore_string_literals: bool = False  # نادیده گرفتن رشته‌های متنی
    ignore_numeric_literals: bool = False  # نادیده گرفتن اعداد
    
    # تنظیمات ساختاری (Structural)
    normalize_whitespace: bool = True  # نرمال‌سازی فاصله‌ها
    remove_comments: bool = True  # حذف کامنت‌ها
    remove_includes: bool = True  # حذف #include ها
    
    # تنظیمات پیشرفته
    ignore_operator_spacing: bool = True  # نادیده گرفتن فاصله اطراف عملگرها
    ignore_bracket_style: bool = True  # نادیده گرفتن سبک آکولاد (کدام خط)
    
    @classmethod
    def smart(cls) -> 'SensitivityConfig':
        """حالت هوشمند: تشخیص تقلب حتی با تغییر نام متغیرها و توابع"""
        return cls(
            ignore_variable_names=True,
            ignore_function_names=True,
            ignore_type_names=False,
            ignore_string_literals=False,
            ignore_numeric_literals=False,
            normalize_whitespace=True,
            remove_comments=True,
            remove_includes=True,
            ignore_operator_spacing=True,
            ignore_bracket_style=True,
        )
    
    @classmethod
    def balanced(cls) -> 'SensitivityConfig':
        """حالت متعادل: فقط نام متغیرها نادیده گرفته می‌شود"""
        return cls(
            ignore_variable_names=True,
            ignore_function_names=False,
            ignore_type_names=False,
            ignore_string_literals=False,
            ignore_numeric_literals=False,
            normalize_whitespace=True,
            remove_comments=True,
            remove_includes=True,
            ignore_operator_spacing=True,
            ignore_bracket_style=True,
        )
    
    @classmethod
    def strict(cls) -> 'SensitivityConfig':
        """حالت سخت‌گیرانه: فقط کدهای کاملاً یکسان تشخیص داده می‌شوند"""
        return cls(
            ignore_variable_names=False,
            ignore_function_names=False,
            ignore_type_names=False,
            ignore_string_literals=False,
            ignore_numeric_literals=False,
            normalize_whitespace=True,
            remove_comments=True,
            remove_includes=True,
            ignore_operator_spacing=True,
            ignore_bracket_style=True,
        )
    
    @classmethod
    def custom(
        cls,
        ignore_variable_names: Optional[bool] = None,
        ignore_function_names: Optional[bool] = None,
        ignore_type_names: Optional[bool] = None,
        ignore_string_literals: Optional[bool] = None,
        ignore_numeric_literals: Optional[bool] = None,
        normalize_whitespace: Optional[bool] = None,
        remove_comments: Optional[bool] = None,
        remove_includes: Optional[bool] = None,
        ignore_operator_spacing: Optional[bool] = None,
        ignore_bracket_style: Optional[bool] = None,
    ) -> 'SensitivityConfig':
        """ایجاد تنظیمات شخصی‌سازی شده"""
        base = cls.smart()  # استفاده از Smart به عنوان پایه
        
        if ignore_variable_names is not None:
            base.ignore_variable_names = ignore_variable_names
        if ignore_function_names is not None:
            base.ignore_function_names = ignore_function_names
        if ignore_type_names is not None:
            base.ignore_type_names = ignore_type_names
        if ignore_string_literals is not None:
            base.ignore_string_literals = ignore_string_literals
        if ignore_numeric_literals is not None:
            base.ignore_numeric_literals = ignore_numeric_literals
        if normalize_whitespace is not None:
            base.normalize_whitespace = normalize_whitespace
        if remove_comments is not None:
            base.remove_comments = remove_comments
        if remove_includes is not None:
            base.remove_includes = remove_includes
        if ignore_operator_spacing is not None:
            base.ignore_operator_spacing = ignore_operator_spacing
        if ignore_bracket_style is not None:
            base.ignore_bracket_style = ignore_bracket_style
        
        return base


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
    IGNORE_VARIABLES = False  # در صورت True، نام متغیرها در مقایسه نادیده گرفته می‌شود (برای سازگاری با نسخه قدیم)
    
    # تنظیمات حساسیت پیشرفته (Advanced Sensitivity Settings)
    # استفاده از حالت متعادل به عنوان پیش‌فرض
    _sensitivity_config: Optional[SensitivityConfig] = None
    
    @classmethod
    def get_sensitivity_config(cls) -> SensitivityConfig:
        """دریافت تنظیمات حساسیت (با مقدار پیش‌فرض)"""
        if cls._sensitivity_config is None:
            cls._sensitivity_config = SensitivityConfig.balanced()
        return cls._sensitivity_config
    
    @classmethod
    def set_sensitivity_config(cls, config: SensitivityConfig):
        """تنظیم پیکربندی حساسیت"""
        cls._sensitivity_config = config
    
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

