"""
ماژول استخراج بازگشتی فایل‌های ZIP (Sandbox Extraction)
این ماژول تمام فایل‌های فشرده را به صورت بازگشتی در پوشه موقت استخراج می‌کند.
"""

import os
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import List, Set, Dict, Optional
import config

# تلاش برای import کتابخانه‌های پشتیبانی RAR/7Z
try:
    import patoolib
    PATOOLIB_AVAILABLE = True
except ImportError:
    PATOOLIB_AVAILABLE = False

try:
    import rarfile
    RARFILE_AVAILABLE = True
except ImportError:
    RARFILE_AVAILABLE = False


class ExtractionError(Exception):
    """خطای سفارشی برای مشکلات استخراج"""
    pass


class ZipExtractor:
    """کلاس مدیریت استخراج فایل‌های ZIP با Sandbox"""
    
    def __init__(self, log_callback=None):
        """
        Args:
            log_callback: تابع برای ثبت خطاها (اختیاری)
        """
        self.log_callback = log_callback
        self.extracted_files: Set[str] = set()  # فایل‌های استخراج شده (جلوگیری از استخراج مجدد)
        self.failed_extractions: List[dict] = []  # لیست استخراج‌های ناموفق
        self.temp_base_dir: Optional[str] = None  # پوشه موقت اصلی
    
    def _should_ignore(self, path: str) -> bool:
        """بررسی اینکه آیا مسیر باید نادیده گرفته شود"""
        path_lower = path.lower()
        for pattern in config.Config.IGNORE_PATTERNS:
            if pattern.lower() in path_lower:
                return True
        return False
    
    def _log_error(self, message: str, student_id: str = "", file_path: str = ""):
        """ثبت خطا در لاگ"""
        error_info = {
            'message': message,
            'student_id': student_id,
            'file_path': file_path
        }
        self.failed_extractions.append(error_info)
        
        if self.log_callback:
            self.log_callback(error_info)
    
    def extract_zip(self, zip_path: str, extract_to: str, student_id: str = "", depth: int = 0) -> bool:
        """
        استخراج یک فایل ZIP در پوشه موقت
        
        Args:
            zip_path: مسیر فایل ZIP
            extract_to: مسیر مقصد استخراج (باید در temp directory باشد)
            student_id: شماره دانشجویی (برای لاگ)
            depth: عمق فعلی استخراج (جلوگیری از حلقه بی‌نهایت)
        
        Returns:
            True اگر استخراج موفق بود، False در غیر این صورت
        """
        if depth > config.Config.MAX_EXTRACTION_DEPTH:
            self._log_error(
                f"حداکثر عمق استخراج ({config.Config.MAX_EXTRACTION_DEPTH}) رسید",
                student_id, zip_path
            )
            return False
        
        # جلوگیری از استخراج مجدد همان فایل
        zip_abs_path = os.path.abspath(zip_path)
        if zip_abs_path in self.extracted_files:
            return True
        
        if not os.path.exists(zip_path):
            self._log_error("فایل ZIP وجود ندارد", student_id, zip_path)
            return False
        
        try:
            # بررسی نوع فایل
            file_ext = os.path.splitext(zip_path)[1].lower()
            
            # ایجاد پوشه مقصد
            os.makedirs(extract_to, exist_ok=True)
            
            # استخراج بر اساس نوع فایل
            if file_ext == '.zip':
                # استخراج ZIP با zipfile استاندارد
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # بررسی رمزگذاری
                    try:
                        zip_ref.testzip()
                    except Exception as e:
                        self._log_error(f"فایل ZIP خراب است: {str(e)}", student_id, zip_path)
                        return False
                    
                    # استخراج تمام فایل‌ها
                    for member in zip_ref.namelist():
                        # نادیده گرفتن فایل‌های سیستم
                        if self._should_ignore(member):
                            continue
                        
                        try:
                            # استخراج فایل
                            zip_ref.extract(member, extract_to)
                            
                            # بررسی اینکه آیا فایل استخراج شده خودش یک ZIP است
                            extracted_path = os.path.join(extract_to, member)
                            
                            if os.path.isfile(extracted_path):
                                # بررسی پسوند فایل
                                file_ext_inner = os.path.splitext(extracted_path)[1].lower()
                                
                                if file_ext_inner in config.Config.ZIP_EXTENSIONS:
                                    # استخراج بازگشتی در پوشه موقت
                                    nested_temp_dir = tempfile.mkdtemp(dir=extract_to)
                                    try:
                                        if self.extract_zip(extracted_path, nested_temp_dir, student_id, depth + 1):
                                            # انتقال فایل‌های استخراج شده به مقصد اصلی
                                            for root, dirs, files in os.walk(nested_temp_dir):
                                                for file in files:
                                                    src = os.path.join(root, file)
                                                    rel_path = os.path.relpath(src, nested_temp_dir)
                                                    dst = os.path.join(extract_to, rel_path)
                                                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                                                    if os.path.exists(src):
                                                        shutil.move(src, dst)
                                    finally:
                                        # پاکسازی پوشه موقت تو در تو
                                        if os.path.exists(nested_temp_dir):
                                            shutil.rmtree(nested_temp_dir, ignore_errors=True)
                                    
                                    # حذف فایل فشرده اصلی بعد از استخراج
                                    try:
                                        if os.path.exists(extracted_path):
                                            os.remove(extracted_path)
                                    except:
                                        pass
                        except Exception as e:
                            # در صورت خطا در استخراج یک فایل، ادامه می‌دهیم
                            self._log_error(f"خطا در استخراج فایل {member}: {str(e)}", student_id, zip_path)
                            continue
                
                    self.extracted_files.add(zip_abs_path)
                    return True
            
            elif file_ext == '.rar':
                # استخراج RAR
                if PATOOLIB_AVAILABLE:
                    try:
                        patoolib.extract_archive(zip_path, outdir=extract_to, verbosity=-1)
                        self.extracted_files.add(zip_abs_path)
                        return True
                    except Exception as e:
                        self._log_error(f"خطا در استخراج RAR با patoolib: {str(e)}", student_id, zip_path)
                        return False
                elif RARFILE_AVAILABLE:
                    try:
                        with rarfile.RarFile(zip_path) as rar_ref:
                            rar_ref.extractall(extract_to)
                        self.extracted_files.add(zip_abs_path)
                        return True
                    except Exception as e:
                        self._log_error(f"خطا در استخراج RAR با rarfile: {str(e)}", student_id, zip_path)
                        return False
                else:
                    self._log_error(
                        "فایل RAR پشتیبانی نمی‌شود. لطفاً 'patoolib' یا 'rarfile' را نصب کنید: pip install patoolib",
                        student_id, zip_path
                    )
                    return False
            
            elif file_ext == '.7z':
                # استخراج 7Z
                if PATOOLIB_AVAILABLE:
                    try:
                        patoolib.extract_archive(zip_path, outdir=extract_to, verbosity=-1)
                        self.extracted_files.add(zip_abs_path)
                        return True
                    except Exception as e:
                        self._log_error(f"خطا در استخراج 7Z: {str(e)}", student_id, zip_path)
                        return False
                else:
                    self._log_error(
                        "فایل 7Z پشتیبانی نمی‌شود. لطفاً 'patoolib' را نصب کنید: pip install patoolib",
                        student_id, zip_path
                    )
                    return False
            
            else:
                self._log_error(f"نوع فایل پشتیبانی نمی‌شود: {file_ext}", student_id, zip_path)
                return False
            
        except zipfile.BadZipFile:
            self._log_error("فایل ZIP معتبر نیست", student_id, zip_path)
            return False
        except RuntimeError as e:
            # احتمالاً رمز دارد
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                self._log_error("فایل ZIP رمز دارد", student_id, zip_path)
            else:
                self._log_error(f"خطای استخراج: {str(e)}", student_id, zip_path)
            return False
        except Exception as e:
            self._log_error(f"خطای غیرمنتظره: {str(e)}", student_id, zip_path)
            return False
    
    def extract_student_zips_to_temp(self, student_dir: str, student_id: str) -> Optional[str]:
        """
        استخراج تمام فایل‌های ZIP یک دانشجو به پوشه موقت
        
        Args:
            student_dir: مسیر پوشه دانشجو (در ROOT_DIR)
            student_id: شماره دانشجویی
        
        Returns:
            مسیر پوشه موقت استخراج شده یا None در صورت خطا
        """
        # ایجاد پوشه موقت برای این دانشجو (بدون context manager - باید دستی پاک شود)
        student_temp_dir = tempfile.mkdtemp(prefix=f'mastergrader_{student_id}_')
        
        try:
            if not os.path.exists(student_dir):
                return None
            
            # کپی فایل‌های ZIP به پوشه موقت (بدون استخراج در ROOT_DIR)
            zip_files_found = False
            for root, dirs, files in os.walk(student_dir):
                # حذف پوشه‌های نادیده گرفته شده از جستجو
                dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in config.Config.ZIP_EXTENSIONS:
                        zip_files_found = True
                        # کپی فایل ZIP به پوشه موقت
                        temp_zip_path = os.path.join(student_temp_dir, file)
                        try:
                            shutil.copy2(file_path, temp_zip_path)
                            # استخراج در پوشه موقت
                            extract_success = self.extract_zip(temp_zip_path, student_temp_dir, student_id)
                            
                            # بررسی تعداد فایل‌های استخراج شده
                            files_after_extract = []
                            for root, dirs, files in os.walk(student_temp_dir):
                                for f in files:
                                    files_after_extract.append(os.path.join(root, f))
                            
                            # حذف فایل ZIP بعد از استخراج (موفق یا ناموفق)
                            try:
                                if os.path.exists(temp_zip_path):
                                    os.remove(temp_zip_path)
                            except:
                                pass
                            
                            if not extract_success:
                                self._log_error(f"خطا در استخراج {file}", student_id, file_path)
                            elif len(files_after_extract) <= 1:
                                # اگر فقط فایل ZIP باقی مانده (یا هیچ فایلی نیست)
                                self._log_error(f"فایل ZIP استخراج نشد یا خالی است: {file}", student_id, file_path)
                        except Exception as e:
                            self._log_error(f"خطا در کپی/استخراج {file}: {str(e)}", student_id, file_path)
                            # حذف فایل ZIP در صورت خطا
                            try:
                                if os.path.exists(temp_zip_path):
                                    os.remove(temp_zip_path)
                            except:
                                pass
            
            # اگر فایل ZIP پیدا نشد، فایل‌های C موجود را کپی کن
            if not zip_files_found:
                c_files_copied = 0
                for root, dirs, files in os.walk(student_dir):
                    dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in config.Config.ACCEPTED_EXTENSIONS:
                            rel_path = os.path.relpath(file_path, student_dir)
                            dest_path = os.path.join(student_temp_dir, rel_path)
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            try:
                                shutil.copy2(file_path, dest_path)
                                c_files_copied += 1
                            except Exception as e:
                                self._log_error(f"خطا در کپی فایل {file}: {str(e)}", student_id, file_path)
                
                if c_files_copied > 0:
                    print(f"    ℹ {c_files_copied} فایل C کپی شد (بدون ZIP)")
            
            # بررسی اینکه آیا فایلی در پوشه موقت وجود دارد
            files_in_temp = []
            for root, dirs, files in os.walk(student_temp_dir):
                for file in files:
                    files_in_temp.append(os.path.join(root, file))
            
            if not files_in_temp:
                print(f"    ⚠ هشدار: پوشه موقت خالی است برای {student_id}")
            else:
                c_files_count = sum(1 for f in files_in_temp if os.path.splitext(f)[1].lower() in config.Config.ACCEPTED_EXTENSIONS)
                if c_files_count == 0:
                    print(f"    ⚠ هشدار: هیچ فایل C در پوشه موقت پیدا نشد (تعداد کل فایل‌ها: {len(files_in_temp)})")
            
            return student_temp_dir
            
        except Exception as e:
            self._log_error(f"خطا در استخراج دانشجو {student_id}: {str(e)}", student_id, student_dir)
            # پاکسازی در صورت خطا
            if os.path.exists(student_temp_dir):
                shutil.rmtree(student_temp_dir, ignore_errors=True)
            return None
    
    def get_failed_extractions(self) -> List[dict]:
        """دریافت لیست استخراج‌های ناموفق"""
        return self.failed_extractions.copy()
    
    def clear_extracted_cache(self):
        """پاک کردن کش فایل‌های استخراج شده"""
        self.extracted_files.clear()
    
    def cleanup_temp_dirs(self, temp_dirs: List[str]):
        """پاکسازی پوشه‌های موقت"""
        for temp_dir in temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass


def extract_student_submissions(root_dir: str, log_callback=None) -> Dict[str, Dict]:
    """
    استخراج تمام فایل‌های ZIP برای تمام دانشجویان در پوشه‌های موقت
    
    Args:
        root_dir: مسیر اصلی پوشه دانشجویان
        log_callback: تابع برای ثبت خطاها
    
    Returns:
        دیکشنری شامل مسیرهای پوشه‌های موقت برای هر دانشجو
    """
    extractor = ZipExtractor(log_callback)
    results = {}
    
    if not os.path.exists(root_dir):
        print(f"⚠ هشدار: مسیر ورودی وجود ندارد: {root_dir}")
        return results
    
    # پیمایش پوشه‌های دانشجویان
    for item in os.listdir(root_dir):
        student_path = os.path.join(root_dir, item)
        
        if os.path.isdir(student_path):
            student_id = item
            print(f"📦 در حال استخراج فایل‌های {student_id}...")
            
            # استخراج به پوشه موقت
            temp_dir = extractor.extract_student_zips_to_temp(student_path, student_id)
            
            if temp_dir:
                results[student_id] = {
                    'temp_path': temp_dir,  # مسیر پوشه موقت
                    'original_path': student_path,  # مسیر اصلی
                    'failed': extractor.get_failed_extractions()
                }
                print(f"  ✓ فایل‌ها در پوشه موقت استخراج شدند")
            else:
                results[student_id] = {
                    'temp_path': None,
                    'original_path': student_path,
                    'failed': extractor.get_failed_extractions()
                }
                print(f"  ⚠ خطا در استخراج")
    
    return results
