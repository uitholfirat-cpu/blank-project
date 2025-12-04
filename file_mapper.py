"""
ماژول نگاشت هوشمند فایل‌ها به سوالات
این ماژول با استفاده از الگوریتم‌های هیوریستیک، فایل‌های نامنظم را به سوالات مربوطه نگاشت می‌کند.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import config


class FileMapper:
    """کلاس نگاشت هوشمند فایل‌ها به سوالات"""

    def __init__(self):
        """مقداردهی اولیه"""
        self.mapping_patterns = self._build_patterns()

    def _build_patterns(self) -> List[Dict]:
        """
        ساخت الگوهای جستجو برای شناسایی سوالات

        Returns:
            لیست الگوهای regex برای هر سوال
        """
        patterns: List[Dict] = []

        # الگوهای مختلف برای شناسایی شماره سوال
        for q_num in range(1, config.Config.NUM_QUESTIONS + 1):
            pattern_set = {
                "question_number": q_num,
                "patterns": [
                    # الگوهای مستقیم: q1, q2, question1, soal1, ...
                    re.compile(rf"\bq{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bquestion{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bsoal{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bsual{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bproblem{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bex{q_num}\b", re.IGNORECASE),
                    re.compile(rf"\bexercise{q_num}\b", re.IGNORECASE),
                    # الگوهای عددی: 1.c, 01.c, (1).c, [1].c
                    re.compile(
                        rf"[^0-9]{q_num}\.{config.Config.ACCEPTED_EXTENSIONS[0]}",
                        re.IGNORECASE,
                    ),
                    re.compile(
                        rf"[^0-9]0{q_num}\.{config.Config.ACCEPTED_EXTENSIONS[0]}",
                        re.IGNORECASE,
                    ),
                    re.compile(rf"\({q_num}\)", re.IGNORECASE),
                    re.compile(rf"\[{q_num}\]", re.IGNORECASE),
                    re.compile(rf"_{q_num}_", re.IGNORECASE),
                    # الگوهای پوشه: folder1, dir1, ...
                    re.compile(rf"[^0-9]{q_num}[^0-9]", re.IGNORECASE),
                ],
            }
            patterns.append(pattern_set)

        return patterns

    def _extract_number_from_path(self, file_path: str) -> Optional[int]:
        """
        استخراج عدد از مسیر فایل
        """
        numbers = re.findall(r"\d+", file_path)

        if numbers:
            for num_str in numbers:
                num = int(num_str)
                if 1 <= num <= config.Config.NUM_QUESTIONS:
                    return num

        return None

    def _match_patterns(self, file_path: str, file_name: str) -> Optional[int]:
        """
        تطبیق الگوها با نام فایل
        """
        for pattern_set in self.mapping_patterns:
            q_num = pattern_set["question_number"]
            patterns = pattern_set["patterns"]

            for pattern in patterns:
                if pattern.search(file_path) or pattern.search(file_name):
                    return q_num

        return None

    def _calculate_confidence_score(
        self, file_path: str, file_name: str, question_num: int
    ) -> float:
        """
        محاسبه امتیاز اطمینان برای نگاشت
        """
        score = 0.0

        if self._match_patterns(file_path, file_name) == question_num:
            score += 0.7

        if str(question_num) in file_name:
            score += 0.2

        path_number = self._extract_number_from_path(file_path)
        if path_number == question_num:
            score += 0.1

        return min(score, 1.0)

    def map_file_to_question(self, file_path: str) -> Optional[Tuple[int, float]]:
        """
        نگاشت یک فایل به سوال

        Returns:
            تاپل (شماره سوال, امتیاز اطمینان) یا None
        """
        if not os.path.exists(file_path):
            return None

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext not in config.Config.ACCEPTED_EXTENSIONS:
            return None

        matched_question = self._match_patterns(file_path, file_name)
        if matched_question:
            confidence = self._calculate_confidence_score(
                file_path, file_name, matched_question
            )
            return matched_question, confidence

        path_number = self._extract_number_from_path(file_path)
        if path_number:
            return path_number, 0.5

        return None

    def map_student_files(
        self, student_dir: str, student_id: str
    ) -> Dict[int, List[str]]:
        """
        نگاشت تمام فایل‌های یک دانشجو به سوالات

        Returns:
            دیکشنری {شماره_سوال: [لیست_مسیرهای_فایل]}
        """
        mapping: Dict[int, List[Tuple[str, float]]] = {}
        unmapped_files: List[str] = []

        if not os.path.exists(student_dir):
            return {}

        # جمع‌آوری تمام فایل‌های C
        c_files: List[str] = []
        for root, dirs, files in os.walk(student_dir):
            dirs[:] = [
                d
                for d in dirs
                if not any(ignore in d.lower() for ignore in config.Config.IGNORE_PATTERNS)
            ]

            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_ext = os.path.splitext(file_name)[1].lower()

                if file_ext in config.Config.ACCEPTED_EXTENSIONS:
                    c_files.append(file_path)

        # Debug: اگر هیچ فایل C پیدا نشد
        if not c_files:
            all_files: List[str] = []
            for root, _dirs, files in os.walk(student_dir):
                for file_name in files:
                    all_files.append(os.path.join(root, file_name))

            if all_files:
                print(
                    f"    [WARN] هیچ فایل C پیدا نشد. "
                    f"فایل‌های موجود: {len(all_files)} فایل"
                )
                for f in all_files[:5]:
                    print(f"      - {os.path.basename(f)}")
            else:
                print("    [WARN] پوشه خالی است یا فایلی وجود ندارد")

        # نگاشت هر فایل
        for file_path in c_files:
            result = self.map_file_to_question(file_path)

            if result:
                question_num, confidence = result
                if question_num not in mapping:
                    mapping[question_num] = []
                mapping[question_num].append((file_path, confidence))
            else:
                unmapped_files.append(file_path)

        # استراتژی Fallback 1
        if (
            len(unmapped_files) == config.Config.NUM_QUESTIONS
            and not mapping
        ):
            unmapped_files.sort()

            for idx, file_path in enumerate(unmapped_files):
                question_num = idx + 1
                if question_num <= config.Config.NUM_QUESTIONS:
                    mapping.setdefault(question_num, []).append(
                        (file_path, 0.3)
                    )

            print(
                f"    [INFO] استراتژی Fallback: "
                f"{len(unmapped_files)} فایل به ترتیب حروف الفبا نگاشت شد"
            )

        # استراتژی Fallback 2
        elif (
            0 < len(unmapped_files) < config.Config.NUM_QUESTIONS
            and not mapping
        ):
            unmapped_files.sort()
            for idx, file_path in enumerate(unmapped_files):
                question_num = idx + 1
                if question_num <= config.Config.NUM_QUESTIONS:
                    mapping.setdefault(question_num, []).append(
                        (file_path, 0.2)
                    )

            print(
                f"    [INFO] استراتژی Fallback 2: "
                f"{len(unmapped_files)} فایل نگاشت شد "
                f"(کمتر از {config.Config.NUM_QUESTIONS} فایل)"
            )

        # انتخاب بهترین فایل برای هر سوال (بالاترین اطمینان)
        final_mapping: Dict[int, List[str]] = {}
        for question_num, candidates in mapping.items():
            candidates.sort(key=lambda x: x[1], reverse=True)
            final_mapping[question_num] = [candidates[0][0]]

        return final_mapping

    def organize_student_files(
        self, student_dir: str, student_id: str, output_dir: str
    ) -> Dict:
        """
        سازماندهی فایل‌های یک دانشجو در پوشه‌های خروجی

        Returns:
            دیکشنری شامل اطلاعات سازماندهی
        """
        import shutil

        mapping = self.map_student_files(student_dir, student_id)

        # جمع‌آوری فایل‌های C برای گزارش
        all_c_files: List[str] = []
        for root, dirs, files in os.walk(student_dir):
            dirs[:] = [
                d
                for d in dirs
                if not any(ignore in d.lower() for ignore in config.Config.IGNORE_PATTERNS)
            ]
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext in config.Config.ACCEPTED_EXTENSIONS:
                    all_c_files.append(file_path)

        mapped_file_paths = set()
        for file_paths in mapping.values():
            mapped_file_paths.update(file_paths)

        unmapped_files = [
            f for f in all_c_files if f not in mapped_file_paths
        ]

        organized: Dict = {
            "student_id": student_id,
            "mapped_files": {},
            "unmapped_files": unmapped_files,
            "total_files": 0,
        }

        # کپی فایل‌های نگاشت شده
        for question_num, file_paths in mapping.items():
            if not file_paths:
                continue

            source_file = file_paths[0]
            dest_dir = os.path.join(output_dir, f"Q{question_num}")
            dest_file = os.path.join(dest_dir, f"{student_id}.c")

            try:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(source_file, dest_file)

                organized["mapped_files"][question_num] = {
                    "source": source_file,
                    "destination": dest_file,
                }
                organized["total_files"] += 1
            except Exception as e:
                print(
                    f"  [WARN] خطا در کپی فایل {source_file}: {str(e)}"
                )

        return organized


def organize_all_students(
    extraction_results: Dict, output_dir: str
) -> Dict:
    """
    سازماندهی فایل‌های تمام دانشجویان از پوشه‌های موقت

    Args:
        extraction_results: نتایج استخراج (از extractor) شامل temp_path
        output_dir: مسیر خروجی

    Returns:
        دیکشنری شامل اطلاعات سازماندهی برای تمام دانشجویان
    """
    mapper = FileMapper()
    results: Dict[str, Dict] = {}

    print("\n" + "=" * 60)
    print("[STEP 2] مرحله سازماندهی فایل‌ها")
    print("=" * 60)

    for student_id, extraction_data in extraction_results.items():
        temp_path = extraction_data.get("temp_path")

        if not temp_path or not os.path.exists(temp_path):
            print(f"\n[WARN] دانشجو {student_id}: پوشه موقت وجود ندارد")
            results[student_id] = {
                "student_id": student_id,
                "mapped_files": {},
                "unmapped_files": [],
                "total_files": 0,
            }
            continue

        print(f"\n[INFO] در حال پردازش {student_id}...")
        print(f"  [INFO] مسیر پوشه موقت: {temp_path}")

        organized = mapper.organize_student_files(
            temp_path, student_id, output_dir
        )
        results[student_id] = organized

        mapped_count = len(organized["mapped_files"])
        print(f"  [+] {mapped_count} فایل سازماندهی شد")

        if organized.get("unmapped_files"):
            print(
                f"  [WARN] {len(organized['unmapped_files'])} فایل نگاشت نشد"
            )

    return results