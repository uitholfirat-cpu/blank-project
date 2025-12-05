"""
ماژول تشخیص تقلب پیشرفته
این ماژول با استفاده از توکن‌سازی و الگوریتم‌های مقایسه، تقلب را تشخیص می‌دهد.
"""

import os
from typing import List, Dict, Tuple, Optional, Set, Literal
from difflib import SequenceMatcher
from collections import defaultdict

import tokenizer
import config

TokenizationMode = Literal["structural", "literal"]

# تلاش برای import networkx برای clustering
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class PlagiarismDetector:
    """کلاس تشخیص تقلب"""

    def __init__(
        self,
        template_tokens: Optional[str] = None,
        mode: TokenizationMode = "structural",
    ):
        """
        Args:
            template_tokens: رشته توکن‌های کد قالب (اختیاری)
            mode: حالت توکن‌سازی:
                - "structural": مقایسه بر اساس ساختار (شناسه‌ها → ID)
                - "literal": مقایسه حساس به نام متغیرها و شناسه‌ها
        """
        self.tokenizer = tokenizer.CTokenizer()
        # کش برای محاسبات تکراری
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        # توکن‌های کد قالب
        self.template_tokens = template_tokens
        # حالت توکن‌سازی برای این instance
        self.mode = mode

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

    def _is_valid_for_comparison(
        self, file_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        بررسی اینکه آیا فایل برای مقایسه معتبر است و توکن‌های آن را برمی‌گرداند

        Args:
            file_path: مسیر فایل

        Returns:
            تاپل (is_valid, token_string) - اگر معتبر نباشد token_string=None
        """
        if not os.path.exists(file_path):
            return False, None

        try:
            with open(
                file_path, "r", encoding="utf-8", errors="ignore"
            ) as f:
                code = f.read()

            # بررسی تعداد توکن (بهینه‌سازی: قبل از توکن‌سازی کامل)
            token_count = self.tokenizer.get_token_count(code, mode=self.mode)
            if token_count < config.Config.MIN_TOKEN_COUNT:
                return False, None

            # توکن‌سازی با درنظرگرفتن حالت انتخاب‌شده
            token_string = self.tokenizer.tokenize(code, mode=self.mode)

            # حذف توکن‌های قالب (Template Subtraction)
            if self.template_tokens and token_string:
                # حذف زیررشته‌های مشترک بین کد دانشجو و کد قالب
                student_tokens = token_string
                template_tokens = self.template_tokens

                # حذف تمام وقوع‌های template_tokens
                while template_tokens in student_tokens:
                    student_tokens = student_tokens.replace(
                        template_tokens, "", 1
                    )

                token_string = student_tokens

            # بررسی مجدد تعداد توکن بعد از حذف قالب
            if len(token_string) < config.Config.MIN_TOKEN_COUNT:
                return False, None

            return True, token_string
        except Exception:
            return False, None

    def compare_two_files(self, file1_path: str, file2_path: str) -> float:
        """
        مقایسه دو فایل و محاسبه شباهت

        Args:
            file1_path: مسیر فایل اول
            file2_path: مسیر فایل دوم

        Returns:
            درصد شباهت (0 تا 100)
        """
        is_valid1, token_str1 = self._is_valid_for_comparison(file1_path)
        is_valid2, token_str2 = self._is_valid_for_comparison(file2_path)

        if not is_valid1 or not is_valid2 or not token_str1 or not token_str2:
            return 0.0

        return self._calculate_similarity(token_str1, token_str2)

    def detect_plagiarism_in_question(
        self, question_dir: str, question_num: int
    ) -> List[Dict]:
        """
        تشخیص تقلب در یک سوال خاص

        Args:
            question_dir: مسیر پوشه سوال
            question_num: شماره سوال

        Returns:
            لیست موارد تقلب شناسایی شده
        """
        plagiarism_cases: List[Dict] = []

        if not os.path.exists(question_dir):
            return plagiarism_cases

        # جمع‌آوری تمام فایل‌های دانشجویان (فقط فایل‌های معتبر)
        student_files: Dict[str, str] = {}
        for file_name in os.listdir(question_dir):
            if file_name.endswith(".c"):
                student_id = os.path.splitext(file_name)[0]
                file_path = os.path.join(question_dir, file_name)

                is_valid, _ = self._is_valid_for_comparison(file_path)
                if is_valid:
                    student_files[student_id] = file_path

        # مقایسه جفتی تمام فایل‌ها
        student_ids = list(student_files.keys())
        total_comparisons = len(student_ids) * (len(student_ids) - 1) // 2

        print(
            f"  [INFO] Comparing {total_comparisons} file pairs for question {question_num}..."
        )

        comparison_count = 0
        for i in range(len(student_ids)):
            for j in range(i + 1, len(student_ids)):
                student1_id = student_ids[i]
                student2_id = student_ids[j]

                file1_path = student_files[student1_id]
                file2_path = student_files[student2_id]

                similarity = self.compare_two_files(file1_path, file2_path)

                if similarity >= config.Config.SIMILARITY_THRESHOLD:
                    plagiarism_cases.append(
                        {
                            "question": question_num,
                            "student1": student1_id,
                            "student2": student2_id,
                            "similarity": similarity,
                            "file1": file1_path,
                            "file2": file2_path,
                        }
                    )

                comparison_count += 1
                if comparison_count and comparison_count % 50 == 0:
                    print(
                        f"    [+] {comparison_count}/{total_comparisons} comparisons completed..."
                    )

        return plagiarism_cases

    def detect_plagiarism_all_questions(
        self, output_dir: str
    ) -> List[Dict]:
        """
        تشخیص تقلب در تمام سوالات

        Args:
            output_dir: مسیر پوشه خروجی

        Returns:
            لیست تمام موارد تقلب
        """
        all_plagiarism_cases: List[Dict] = []

        print("\n" + "=" * 60)
        print("[STEP] Plagiarism detection step")
        print("=" * 60)

        for question_num in range(1, config.Config.NUM_QUESTIONS + 1):
            question_dir = os.path.join(output_dir, f"Q{question_num}")

            if os.path.exists(question_dir):
                print(f"\n[INFO] Checking question {question_num}...")
                cases = self.detect_plagiarism_in_question(
                    question_dir, question_num
                )
                all_plagiarism_cases.extend(cases)

                if cases:
                    print(
                        f"  [WARN] {len(cases)} potential plagiarism cases detected"
                    )
                else:
                    print("  [+] No plagiarism cases detected")

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

        G = nx.Graph()

        # اضافه کردن یال‌ها برای هر جفت متقلب
        for case in plagiarism_cases:
            student1 = case["student1"]
            student2 = case["student2"]
            G.add_edge(
                student1,
                student2,
                similarity=case["similarity"],
                question=case["question"],
            )

        clusters: List[Dict] = []
        for component in nx.connected_components(G):
            if len(component) > 1:
                cluster_students = sorted(list(component))
                clusters.append(
                    {
                        "students": cluster_students,
                        "size": len(cluster_students),
                        "cluster_id": len(clusters) + 1,
                    }
                )

        return clusters

    def _find_clusters_simple(self, plagiarism_cases: List[Dict]) -> List[Dict]:
        """
        پیدا کردن خوشه‌ها بدون networkx (fallback)

        Args:
            plagiarism_cases: لیست موارد تقلب

        Returns:
            لیست خوشه‌ها
        """
        connections: Dict[str, Set[str]] = defaultdict(set)

        for case in plagiarism_cases:
            student1 = case["student1"]
            student2 = case["student2"]
            connections[student1].add(student2)
            connections[student2].add(student1)

        visited: Set[str] = set()
        clusters: List[Dict] = []
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
                    clusters.append(
                        {
                            "students": sorted(list(cluster)),
                            "size": len(cluster),
                            "cluster_id": cluster_id,
                        }
                    )
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
        stats: Dict = {
            "total_cases": len(plagiarism_cases),
            "by_question": defaultdict(int),
            "by_student": defaultdict(int),
            "similarity_distribution": {
                "85-90": 0,
                "90-95": 0,
                "95-99": 0,
                "99-100": 0,
            },
            "clusters": [],
        }

        for case in plagiarism_cases:
            # آمار بر اساس سوال
            stats["by_question"][case["question"]] += 1

            # آمار بر اساس دانشجو
            stats["by_student"][case["student1"]] += 1
            stats["by_student"][case["student2"]] += 1

            similarity = case["similarity"]
            if 85 <= similarity < 90:
                stats["similarity_distribution"]["85-90"] += 1
            elif 90 <= similarity < 95:
                stats["similarity_distribution"]["90-95"] += 1
            elif 95 <= similarity < 99:
                stats["similarity_distribution"]["95-99"] += 1
            elif similarity >= 99:
                stats["similarity_distribution"]["99-100"] += 1

        stats["clusters"] = self.find_clusters(plagiarism_cases)

        return stats


def load_template_tokens(
    template_path: Optional[str],
    mode: TokenizationMode = "structural",
) -> Optional[str]:
    """
    بارگذاری و توکن‌سازی فایل قالب

    Args:
        template_path: مسیر فایل قالب
        mode: حالت توکن‌سازی که برای مقایسه دانشجوها نیز استفاده می‌شود

    Returns:
        رشته توکن‌های قالب یا None
    """
    if not template_path or not os.path.exists(template_path):
        return None

    try:
        return tokenizer.tokenize_file(template_path, mode=mode)
    except Exception as e:
        print(f"[WARN] Error loading template file: {str(e)}")
        return None


def detect_plagiarism(
    output_dir: str,
    template_path: Optional[str] = None,
    mode: TokenizationMode = "structural",
) -> Tuple[List[Dict], Dict]:
    """
    تابع اصلی برای تشخیص تقلب

    Args:
        output_dir: مسیر پوشه خروجی
        template_path: مسیر فایل قالب (اختیاری)
        mode: حالت توکن‌سازی موتور:
            - "structural": Smart mode (مقاوم در برابر تغییر نام متغیرها)
            - "literal": Strict mode (فقط کپی‌های مستقیم)

    Returns:
        تاپل (لیست موارد تقلب, آمار)
    """
    # بارگذاری توکن‌های قالب بر اساس همان حالت توکن‌سازی
    template_tokens = load_template_tokens(template_path, mode=mode)
    if template_tokens:
        print(f"[+] Template file loaded: {template_path}")

    detector = PlagiarismDetector(
        template_tokens=template_tokens,
        mode=mode,
    )
    plagiarism_cases = detector.detect_plagiarism_all_questions(output_dir)
    statistics = detector.get_statistics(plagiarism_cases)

    # نمایش اطلاعات خوشه‌ها
    if statistics["clusters"]:
        print(
            f"\n[INFO] {len(statistics['clusters'])} plagiarism clusters detected:"
        )
        for cluster in statistics["clusters"]:
            print(
                f"  - Cluster #{cluster['cluster_id']}: "
                f"{cluster['size']} students - {', '.join(cluster['students'])}"
            )

    return plagiarism_cases, statistics