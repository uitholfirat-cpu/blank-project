"""
ماژول توکن‌سازی پیشرفته کد C
این ماژول کد C را به توکن‌های معنادار تبدیل می‌کند تا تشخیص تقلب دقیق‌تر شود.
"""

import re
from typing import List, Set, Tuple
import config


class CTokenizer:
    """کلاس توکن‌سازی کد C"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.keywords = config.Config.C_KEYWORDS
        self.operators = config.Config.C_OPERATORS
        self._build_regex_patterns()
    
    def _build_regex_patterns(self):
        """ساخت الگوهای regex برای تجزیه کد"""
        # الگو برای شناسایی کامنت‌های تک خطی
        self.single_line_comment = re.compile(r'//.*?$', re.MULTILINE)
        
        # الگو برای شناسایی کامنت‌های چند خطی
        self.multi_line_comment = re.compile(r'/\*.*?\*/', re.DOTALL)
        
        # الگو برای شناسایی #include
        self.include_pattern = re.compile(r'#include\s*[<"].*?[>"]', re.IGNORECASE)
        
        # الگو برای شناسایی رشته‌های متنی
        self.string_pattern = re.compile(r'"[^"]*"|\'[^\']*\'')
        
        # الگو برای شناسایی اعداد (اعشار، صحیح، اعشاری)
        self.number_pattern = re.compile(r'\b\d+\.?\d*\b')
        
        # الگو برای شناسایی شناسه‌ها (متغیرها و توابع)
        self.identifier_pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
    
    def _remove_comments(self, code: str) -> str:
        """
        حذف کامنت‌ها از کد
        
        Args:
            code: کد C
        
        Returns:
            کد بدون کامنت
        """
        if not config.Config.REMOVE_COMMENTS:
            return code
        
        # حذف کامنت‌های چند خطی
        code = self.multi_line_comment.sub('', code)
        
        # حذف کامنت‌های تک خطی
        code = self.single_line_comment.sub('', code)
        
        return code
    
    def _remove_includes(self, code: str) -> str:
        """
        حذف دستورات #include
        
        Args:
            code: کد C
        
        Returns:
            کد بدون #include
        """
        if not config.Config.REMOVE_INCLUDES:
            return code
        
        code = self.include_pattern.sub('', code)
        return code
    
    def _normalize_whitespace(self, code: str) -> str:
        """
        نرمال‌سازی فاصله‌های خالی
        
        Args:
            code: کد C
        
        Returns:
            کد با فاصله‌های نرمال شده
        """
        if not config.Config.NORMALIZE_WHITESPACE:
            return code
        
        # تبدیل تمام فاصله‌های خالی به یک فاصله
        code = re.sub(r'\s+', ' ', code)
        
        # حذف فاصله‌های اضافی اطراف عملگرها و نمادها
        code = re.sub(r'\s*([+\-*/%=<>!&|^~,;:()\[\]{}])\s*', r'\1', code)
        
        return code
    
    def _is_keyword(self, word: str) -> bool:
        """بررسی اینکه آیا کلمه یک کلمه کلیدی C است"""
        return word.lower() in self.keywords
    
    def _is_operator(self, char: str) -> bool:
        """بررسی اینکه آیا کاراکتر یک عملگر است"""
        return char in self.operators
    
    def _tokenize_code(self, code: str) -> List[str]:
        """
        تبدیل کد به لیست توکن‌ها
        
        Args:
            code: کد C
        
        Returns:
            لیست توکن‌ها
        """
        tokens = []
        i = 0
        code_len = len(code)
        
        while i < code_len:
            # رد شدن از فاصله‌های خالی
            if code[i].isspace():
                i += 1
                continue
            
            # بررسی عملگرهای چند کاراکتری
            matched = False
            for op_len in [3, 2, 1]:  # بررسی از طولانی‌ترین به کوتاه‌ترین
                if i + op_len <= code_len:
                    candidate = code[i:i+op_len]
                    if candidate in self.operators:
                        tokens.append(candidate)
                        i += op_len
                        matched = True
                        break
            
            if matched:
                continue
            
            # بررسی اعداد
            num_match = self.number_pattern.match(code, i)
            if num_match:
                tokens.append('NUM')
                i = num_match.end()
                continue
            
            # بررسی رشته‌ها
            str_match = self.string_pattern.match(code, i)
            if str_match:
                tokens.append('STR')
                i = str_match.end()
                continue
            
            # بررسی شناسه‌ها (متغیرها و توابع)
            id_match = self.identifier_pattern.match(code, i)
            if id_match:
                word = id_match.group()
                
                if self._is_keyword(word):
                    # کلمات کلیدی را حفظ می‌کنیم
                    tokens.append(word.upper())
                else:
                    # شناسه‌های کاربر را به ID تبدیل می‌کنیم
                    tokens.append('ID')
                
                i = id_match.end()
                continue
            
            # کاراکترهای دیگر (مثل نمادهای خاص)
            tokens.append(code[i])
            i += 1
        
        return tokens
    
    def _find_function_blocks(self, code: str) -> List[Tuple[str, int, int]]:
        """
        پیدا کردن بلوک‌های توابع با استفاده از شمارش آکولاد
        
        Args:
            code: کد C
        
        Returns:
            لیست تاپل‌های (نام_تابع, شروع, پایان)
        """
        functions = []
        
        # الگو برای شناسایی شروع توابع (انواع مختلف return type)
        function_start_pattern = re.compile(
            r'\b(?:int|void|char|float|double|long|short|unsigned|signed|struct\s+\w+|enum\s+\w+)\s+'
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )
        
        # پیدا کردن تمام شروع توابع
        for match in function_start_pattern.finditer(code):
            func_name = match.group(1)
            start_pos = match.start()
            
            # پیدا کردن پایان تابع با شمارش آکولاد
            brace_count = 0
            in_string = False
            string_char = None
            i = match.end() - 1  # شروع از '{'
            
            while i < len(code):
                char = code[i]
                
                # مدیریت رشته‌ها
                if char in ['"', "'"] and (i == 0 or code[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                
                # شمارش آکولاد (فقط خارج از رشته)
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # پایان تابع پیدا شد
                            end_pos = i + 1
                            functions.append((func_name, start_pos, end_pos))
                            break
                
                i += 1
        
        return functions
    
    def _sort_functions(self, code: str) -> str:
        """
        مرتب‌سازی توابع بر اساس نام (برای مقاومت در برابر تغییر ترتیب)
        
        این پیاده‌سازی با استفاده از Regex و شمارش آکولاد، توابع را شناسایی
        و بر اساس نام مرتب می‌کند. اگرچه کامل نیست (مثل pycparser)، اما
        برای اکثر موارد کافی است.
        
        Args:
            code: کد C
        
        Returns:
            کد با توابع مرتب شده
        """
        try:
            # پیدا کردن تمام توابع
            functions = self._find_function_blocks(code)
            
            if len(functions) < 2:
                # اگر کمتر از 2 تابع داریم، نیازی به مرتب‌سازی نیست
                return code
            
            # مرتب‌سازی بر اساس نام تابع
            functions_sorted = sorted(functions, key=lambda x: x[0].lower())
            
            # استخراج بخش‌های کد (قبل از اولین تابع، بین توابع، بعد از آخرین تابع)
            result_parts = []
            last_end = 0
            
            # کد قبل از اولین تابع
            if functions_sorted[0][1] > 0:
                result_parts.append(code[0:functions_sorted[0][1]])
            
            # اضافه کردن توابع مرتب شده
            for i, (func_name, start, end) in enumerate(functions_sorted):
                result_parts.append(code[start:end])
                
                # کد بین توابع
                if i < len(functions_sorted) - 1:
                    next_start = functions_sorted[i + 1][1]
                    if end < next_start:
                        result_parts.append(code[end:next_start])
            
            # کد بعد از آخرین تابع
            if functions_sorted[-1][2] < len(code):
                result_parts.append(code[functions_sorted[-1][2]:])
            
            return ''.join(result_parts)
            
        except Exception as e:
            # در صورت خطا، کد اصلی را برمی‌گردانیم
            # این یک fallback است تا برنامه crash نکند
            return code
    
    def tokenize(self, code: str) -> str:
        """
        توکن‌سازی کامل کد C
        
        Args:
            code: کد C خام
        
        Returns:
            رشته توکن‌های نرمال شده
        """
        if not code or not code.strip():
            return ""
        
        # مرحله 1: حذف کامنت‌ها
        code = self._remove_comments(code)
        
        # مرحله 2: حذف #include ها
        code = self._remove_includes(code)
        
        # مرحله 3: مرتب‌سازی توابع (برای مقاومت در برابر تغییر ترتیب)
        code = self._sort_functions(code)
        
        # مرحله 4: نرمال‌سازی فاصله‌ها
        code = self._normalize_whitespace(code)
        
        # مرحله 5: توکن‌سازی
        tokens = self._tokenize_code(code)
        
        # مرحله 6: تبدیل به رشته (بدون فاصله برای مقایسه دقیق‌تر)
        token_string = ''.join(tokens)
        
        return token_string
    
    def get_token_count(self, code: str) -> int:
        """
        شمارش تعداد توکن‌ها
        
        Args:
            code: کد C
        
        Returns:
            تعداد توکن‌ها
        """
        token_string = self.tokenize(code)
        return len(token_string)
    
    def is_code_valid_for_plagiarism_check(self, code: str) -> bool:
        """
        بررسی اینکه آیا کد برای بررسی تقلب معتبر است
        
        Args:
            code: کد C
        
        Returns:
            True اگر کد معتبر باشد
        """
        token_count = self.get_token_count(code)
        return token_count >= config.Config.MIN_TOKEN_COUNT


def tokenize_file(file_path: str) -> str:
    """
    توکن‌سازی یک فایل C
    
    Args:
        file_path: مسیر فایل
    
    Returns:
        رشته توکن‌ها
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        tokenizer = CTokenizer()
        return tokenizer.tokenize(code)
    except Exception as e:
        print(f"⚠ خطا در خواندن فایل {file_path}: {str(e)}")
        return ""


def get_token_count_from_file(file_path: str) -> int:
    """
    شمارش توکن‌های یک فایل
    
    Args:
        file_path: مسیر فایل
    
    Returns:
        تعداد توکن‌ها
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        tokenizer = CTokenizer()
        return tokenizer.get_token_count(code)
    except Exception:
        return 0

