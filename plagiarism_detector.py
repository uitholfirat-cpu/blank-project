"""
ماژول تشخیص تقلب پیشرفته
این ماژول با استفاده از توکن‌سازی و الگوریتم‌های مقایسه، تقلب را تشخیص می‌دهد.
"""

import os
from typing import List, Dict, Tuple, Optional, Set
from difflib import SequenceMatcher
from collections import defaultdict
import tokenizer
import config

# تلاش برای import networkx برای clustering
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class PlagiarismDetector:
    """کلاس تشخیص تقلب"""
    
    def __init__(self, template_tokens: Optional[str] = None):
        """
        Args:
            template_tokens: رشته توکن‌های کد قالب (اختیاری)
        """
        self.tokenizer = tokenizer.CTokenizer()
        self.similarity_cache: Dict[Tuple[str, str], float] = {}  # کش برای محاسبات تکراری
        self.template_tokens = template_tokens  # توکن‌های کد قالب
    
    def _calculate_similarity(self, token_str1: str, token_str2: str) -> float:
        """
        محاسبه شباهت بین دو رشته توکن
        
        Args:
            token_str1: رشته توکن اول
            token_str2: رشته توکن دوم
        
        Returns:
            درصد شباهت (0 تا 100)
        """
        if not token_str1 or not token_str2:
            return 0.0
        
        # استفاده از کش برای جلوگیری از محاسبات تکراری
        cache_key = tuple(sorted([token_str1, token_str2]))
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # محاسبه شباهت با SequenceMatcher
        similarity = SequenceMatcher(None, token_str1, token_str2).ratio()
        similarity_percent = similarity * 100.0
        
        # ذخیره در کش
        self.similarity_cache[cache_key] = similarity_percent
        
        return similarity_percent
    
    def _is_valid_for_comparison(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        بررسی اینکه آیا فایل برای مقایسه معتبر است و توکن‌های آن را برمی‌گرداند
        
        Args:
            file_path: مسیر فایل
        
        Returns:
            تاپل (is_valid, token_string) - اگر معتبر نباشد token_string=None
        """
        if not os.path.exists(file_path):
            return (False, None)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # بررسی تعداد توکن (بهینه‌سازی: قبل از توکن‌سازی کامل)
            token_count = self.tokenizer.get_token_count(code)
            if token_count < config.Config.MIN_TOKEN_COUNT:
                return (False, None)
            
            # توکن‌سازی
            token_string = self.tokenizer.tokenize(code)
            
            # حذف توکن‌های قالب (Template Subtraction)
            if self.template_tokens and token_string:
                # حذف توکن‌های قالب از کد دانشجو
                # استراتژی: حذف زیررشته‌های مشترک
                # این یک روش ساده است - می‌توان با الگوریتم‌های پیشرفته‌تر بهبود داد
                student_tokens = token_string
                template_tokens = self.template_tokens
                
                # اگر توکن‌های قالب در کد دانشجو وجود دارد، حذف می‌کنیم
                # این کار را به صورت بازگشتی انجام می‌دهیم تا تمام موارد حذف شوند
                while template_tokens in student_tokens:
                    student_tokens = student_tokens.replace(template_tokens, '', 1)
                
                token_string = student_tokens
            
            # بررسی مجدد تعداد توکن بعد از حذف قالب
            if len(token_string) < config.Config.MIN_TOKEN_COUNT:
                return (False, None)
            
            return (True, token_string)
        except Exception:
            return (False, None)
    
    def compare_two_files(self, file1_path: str, file2_path: str) -> float:
        """
        مقایسه دو فایل و محاسبه شباهت
        
        Args:
            file1_path: مسیر فایل اول
            file2_path: مسیر فایل دوم
        
        Returns:
            درصد شباهت (0 تا 100)
        """
        # بررسی اعتبار و دریافت توکن‌ها (بهینه‌سازی: فقط یک بار توکن‌سازی)
        is_valid1, token_str1 = self._is_valid_for_comparison(file1_path)
        is_valid2, token_str2 = self._is_valid_for_comparison(file2_path)
        
        if not is_valid1 or not is_valid2 or not token_str1 or not token_str2:
            return 0.0
        
        # محاسبه شباهت
        similarity = self._calculate_similarity(token_str1, token_str2)
        
        return similarity
    
    def detect_plagiarism_in_question(self, question_dir: str, question_num: int) -> List[Dict]:
        """
        تشخیص تقلب در یک سوال خاص
        
        Args:
            question_dir: مسیر پوشه سوال
            question_num: شماره سوال
        
        Returns:
            لیست موارد تقلب شناسایی شده
        """
        plagiarism_cases = []
        
        if not os.path.exists(question_dir):
            return plagiarism_cases
        
        # جمع‌آوری تمام فایل‌های دانشجویان (بهینه‌سازی: فقط فایل‌های معتبر)
        student_files = {}
        for file_name in os.listdir(question_dir):
            if file_name.endswith('.c'):
                student_id = os.path.splitext(file_name)[0]
                file_path = os.path.join(question_dir, file_name)
                
                is_valid, _ = self._is_valid_for_comparison(file_path)
                if is_valid:
                    student_files[student_id] = file_path
        
        # مقایسه جفتی تمام فایل‌ها
        student_ids = list(student_files.keys())
        total_comparisons = len(student_ids) * (len(student_ids) - 1) // 2
        
        print(f"  🔍 در حال مقایسه {total_comparisons} جفت فایل برای سوال {question_num}...")
        
        comparison_count = 0
        for i in range(len(student_ids)):
            for j in range(i + 1, len(student_ids)):
                student1_id = student_ids[i]
                student2_id = student_ids[j]
                
                file1_path = student_files[student1_id]
                file2_path = student_files[student2_id]
                
                # محاسبه شباهت
                similarity = self.compare_two_files(file1_path, file2_path)
                
                # اگر شباهت از آستانه بیشتر باشد
                if similarity >= config.Config.SIMILARITY_THRESHOLD:
                    plagiarism_cases.append({
                        'question': question_num,
                        'student1': student1_id,
                        'student2': student2_id,
                        'similarity': similarity,
                        'file1': file1_path,
                        'file2': file2_path
                    })
                
                comparison_count += 1
                if comparison_count % 50 == 0:
                    print(f"    ✓ {comparison_count}/{total_comparisons} مقایسه انجام شد...")
        
        return plagiarism_cases
    
    def detect_plagiarism_all_questions(self, output_dir: str) -> List[Dict]:
        """
        تشخیص تقلب در تمام سوالات
        
        Args:
            output_dir: مسیر پوشه خروجی
        
        Returns:
            لیست تمام موارد تقلب
        """
        all_plagiarism_cases = []
        
        print("\n" + "="*60)
        print("🔎 مرحله تشخیص تقلب")
        print("="*60)
        
        for question_num in range(1, config.Config.NUM_QUESTIONS + 1):
            question_dir = os.path.join(output_dir, f"Q{question_num}")
            
            if os.path.exists(question_dir):
                print(f"\n📝 بررسی سوال {question_num}...")
                cases = self.detect_plagiarism_in_question(question_dir, question_num)
                all_plagiarism_cases.extend(cases)
                
                if cases:
                    print(f"  ⚠ {len(cases)} مورد تقلب احتمالی شناسایی شد")
                else:
                    print(f"  ✓ هیچ مورد تقلبی شناسایی نشد")
        
        return all_plagiarism_cases
    
    def find_clusters(self, plagiarism_cases: List[Dict]) -> List[Dict]:
        """
        پیدا کردن خوشه‌های تقلب با استفاده از گراف (Connected Components)
        
        Args:
            plagiarism_cases: لیست موارد تقلب
        
        Returns:
            لیست خوشه‌ها (هر خوشه شامل لیست دانشجویان)
        """
        if not NETWORKX_AVAILABLE:
            # اگر networkx نصب نشده، خوشه‌های ساده با dictionary می‌سازیم
            return self._find_clusters_simple(plagiarism_cases)
        
        # ساخت گراف
        G = nx.Graph()
        
        # اضافه کردن یال‌ها (edge) برای هر جفت متقلب
        for case in plagiarism_cases:
            student1 = case['student1']
            student2 = case['student2']
            G.add_edge(student1, student2, similarity=case['similarity'], question=case['question'])
        
        # پیدا کردن اجزای متصل (Connected Components)
        clusters = []
        for component in nx.connected_components(G):
            if len(component) > 1:  # فقط خوشه‌های با حداقل 2 نفر
                cluster_students = sorted(list(component))
                clusters.append({
                    'students': cluster_students,
                    'size': len(cluster_students),
                    'cluster_id': len(clusters) + 1
                })
        
        return clusters
    
    def _find_clusters_simple(self, plagiarism_cases: List[Dict]) -> List[Dict]:
        """
        پیدا کردن خوشه‌ها بدون networkx (fallback)
        
        Args:
            plagiarism_cases: لیست موارد تقلب
        
        Returns:
            لیست خوشه‌ها
        """
        # ساخت یک dictionary برای نگهداری ارتباطات
        connections: Dict[str, Set[str]] = defaultdict(set)
        
        for case in plagiarism_cases:
            student1 = case['student1']
            student2 = case['student2']
            connections[student1].add(student2)
            connections[student2].add(student1)
        
        # پیدا کردن خوشه‌ها با DFS ساده
        visited: Set[str] = set()
        clusters = []
        cluster_id = 1
        
        def dfs(student: str, current_cluster: Set[str]):
            """DFS برای پیدا کردن تمام دانشجویان مرتبط"""
            if student in visited:
                return
            visited.add(student)
            current_cluster.add(student)
            
            for connected in connections[student]:
                if connected not in visited:
                    dfs(connected, current_cluster)
        
        for student in connections:
            if student not in visited:
                cluster = set()
                dfs(student, cluster)
                if len(cluster) > 1:
                    clusters.append({
                        'students': sorted(list(cluster)),
                        'size': len(cluster),
                        'cluster_id': cluster_id
                    })
                    cluster_id += 1
        
        return clusters
    
    def get_statistics(self, plagiarism_cases: List[Dict]) -> Dict:
        """
        محاسبه آمار تقلب
        
        Args:
            plagiarism_cases: لیست موارد تقلب
        
        Returns:
            دیکشنری آمار
        """
        stats = {
            'total_cases': len(plagiarism_cases),
            'by_question': defaultdict(int),
            'by_student': defaultdict(int),
            'similarity_distribution': {
                '85-90': 0,
                '90-95': 0,
                '95-99': 0,
                '99-100': 0
            },
            'clusters': []
        }
        
        for case in plagiarism_cases:
            # آمار بر اساس سوال
            stats['by_question'][case['question']] += 1
            
            # آمار بر اساس دانشجو
            stats['by_student'][case['student1']] += 1
            stats['by_student'][case['student2']] += 1
            
            # توزیع شباهت
            similarity = case['similarity']
            if 85 <= similarity < 90:
                stats['similarity_distribution']['85-90'] += 1
            elif 90 <= similarity < 95:
                stats['similarity_distribution']['90-95'] += 1
            elif 95 <= similarity < 99:
                stats['similarity_distribution']['95-99'] += 1
            elif similarity >= 99:
                stats['similarity_distribution']['99-100'] += 1
        
        # پیدا کردن خوشه‌ها
        clusters = self.find_clusters(plagiarism_cases)
        stats['clusters'] = clusters
        
        return stats


def load_template_tokens(template_path: Optional[str]) -> Optional[str]:
    """
    بارگذاری و توکن‌سازی فایل قالب
    
    Args:
        template_path: مسیر فایل قالب
    
    Returns:
        رشته توکن‌های قالب یا None
    """
    if not template_path or not os.path.exists(template_path):
        return None
    
    try:
        return tokenizer.tokenize_file(template_path)
    except Exception as e:
        print(f"⚠ خطا در بارگذاری فایل قالب: {str(e)}")
        return None


def detect_plagiarism(output_dir: str, template_path: Optional[str] = None) -> Tuple[List[Dict], Dict]:
    """
    تابع اصلی برای تشخیص تقلب
    
    Args:
        output_dir: مسیر پوشه خروجی
        template_path: مسیر فایل قالب (اختیاری)
    
    Returns:
        تاپل (لیست موارد تقلب, آمار)
    """
    # بارگذاری توکن‌های قالب
    template_tokens = load_template_tokens(template_path)
    if template_tokens:
        print(f"✓ فایل قالب بارگذاری شد: {template_path}")
    
    detector = PlagiarismDetector(template_tokens=template_tokens)
    plagiarism_cases = detector.detect_plagiarism_all_questions(output_dir)
    statistics = detector.get_statistics(plagiarism_cases)
    
    # نمایش اطلاعات خوشه‌ها
    if statistics['clusters']:
        print(f"\n📊 {len(statistics['clusters'])} خوشه تقلب شناسایی شد:")
        for cluster in statistics['clusters']:
            print(f"  • Cluster #{cluster['cluster_id']}: {cluster['size']} دانشجو - {', '.join(cluster['students'])}")
    
    return plagiarism_cases, statistics

