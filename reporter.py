"""
ماژول گزارش‌دهی و خروجی
این ماژول گزارش‌های CSV، HTML و خروجی کنسول را تولید می‌کند.
"""

import os
import csv
from typing import List, Dict, Optional
from datetime import datetime
from difflib import HtmlDiff

import config


class Reporter:
    """کلاس تولید گزارش"""

    def __init__(self):
        """مقداردهی اولیه"""
        self.report_file = config.Config.get_report_file_path()
        self.html_reports_dir = config.Config.get_html_reports_dir()
        os.makedirs(self.html_reports_dir, exist_ok=True)

    def print_console_summary(
        self, plagiarism_cases: List[Dict], statistics: Dict
    ):
        """
        چاپ خلاصه در کنسول
        """
        if not config.Config.CONSOLE_OUTPUT_ENABLED:
            return

        print("\n" + "=" * 80)
        print("[SUMMARY] گزارش خلاصه تشخیص تقلب")
        print("=" * 80)

        # آمار کلی
        print("\n[STATS] آمار کلی:")
        print(
            f"  • تعداد کل موارد تقلب احتمالی: {statistics['total_cases']}"
        )

        # آمار بر اساس سوال
        if statistics["by_question"]:
            print("\n[STATS] توزیع بر اساس سوال:")
            for question_num in sorted(statistics["by_question"].keys()):
                count = statistics["by_question"][question_num]
                print(f"  • سوال {question_num}: {count} مورد")

        # توزیع شباهت
        if statistics["similarity_distribution"]:
            print("\n[STATS] توزیع درصد شباهت:")
            dist = statistics["similarity_distribution"]
            for range_name, count in dist.items():
                if count > 0:
                    print(f"  • {range_name}%: {count} مورد")

        # دانشجویان مشکوک
        if statistics["by_student"]:
            print("\n[WARN] دانشجویان با بیشترین موارد تقلب:")
            sorted_students = sorted(
                statistics["by_student"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            for student_id, count in sorted_students:
                print(f"  • {student_id}: {count} مورد")

        # خوشه‌های تقلب
        if statistics.get("clusters"):
            print("\n[INFO] خوشه‌های تقلب شناسایی شده:")
            for cluster in statistics["clusters"]:
                students_str = ", ".join(cluster["students"])
                print(
                    f"  • Cluster #{cluster['cluster_id']}: "
                    f"{cluster['size']} دانشجو - [{students_str}]"
                )

        # جزئیات موارد تقلب
        if plagiarism_cases:
            print("\n[DETAIL] جزئیات موارد تقلب (نمونه 10 مورد اول):")
            print("-" * 80)
            print(
                f"{'سوال':<8} {'دانشجو 1':<15} "
                f"{'دانشجو 2':<15} {'شباهت %':<12}"
            )
            print("-" * 80)

            for case in plagiarism_cases[:10]:
                print(
                    f"Q{case['question']:<7} "
                    f"{case['student1']:<15} "
                    f"{case['student2']:<15} "
                    f"{case['similarity']:.2f}%"
                )

            if len(plagiarism_cases) > 10:
                print(
                    f"\n  ... و {len(plagiarism_cases) - 10} مورد دیگر"
                )

        print("\n" + "=" * 80)

    def generate_detailed_report(
        self, plagiarism_cases: List[Dict], statistics: Dict
    ) -> bool:
        """
        تولید گزارش تفصیلی متنی
        """
        try:
            report_path = os.path.join(
                config.Config.OUTPUT_DIR, "Detailed_Report.txt"
            )

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("گزارش تفصیلی تشخیص تقلب\n")
                f.write("=" * 80 + "\n")
                f.write(
                    f"تاریخ تولید: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(
                    f"آستانه شباهت: {config.Config.SIMILARITY_THRESHOLD}%\n"
                )
                f.write(
                    f"حداقل تعداد توکن: {config.Config.MIN_TOKEN_COUNT}\n"
                )
                f.write("\n" + "=" * 80 + "\n\n")

                # آمار کلی
                f.write("[STATS] آمار کلی:\n")
                f.write(
                    f"  تعداد کل موارد تقلب احتمالی: "
                    f"{statistics['total_cases']}\n\n"
                )

                # آمار بر اساس سوال
                if statistics["by_question"]:
                    f.write("[STATS] توزیع بر اساس سوال:\n")
                    for question_num in sorted(
                        statistics["by_question"].keys()
                    ):
                        count = statistics["by_question"][question_num]
                        f.write(f"  سوال {question_num}: {count} مورد\n")
                    f.write("\n")

                # خوشه‌های تقلب
                if statistics.get("clusters"):
                    f.write("[INFO] خوشه‌های تقلب:\n")
                    for cluster in statistics["clusters"]:
                        students_str = ", ".join(cluster["students"])
                        f.write(
                            f"  Cluster #{cluster['cluster_id']}: "
                            f"{cluster['size']} دانشجو - [{students_str}]\n"
                        )
                    f.write("\n")

                # جزئیات تمام موارد
                if plagiarism_cases:
                    f.write("[DETAIL] جزئیات تمام موارد تقلب:\n")
                    f.write("-" * 80 + "\n")

                    current_question: Optional[int] = None
                    for case in sorted(
                        plagiarism_cases,
                        key=lambda x: (x["question"], -x["similarity"]),
                    ):
                        if current_question != case["question"]:
                            current_question = case["question"]
                            f.write(f"\nسوال {current_question}:\n")
                            f.write("-" * 80 + "\n")

                        f.write(
                            f"  • {case['student1']} <-> {case['student2']}: "
                            f"{case['similarity']:.2f}%\n"
                        )

            print(f"[+] گزارش تفصیلی ذخیره شد: {report_path}")
            return True

        except Exception as e:
            print(f"[ERROR] خطا در تولید گزارش تفصیلی: {str(e)}")
            return False

    def generate_html_diff(self, case: Dict) -> Optional[str]:
        """
        تولید فایل HTML diff برای یک جفت متقلب

        Returns:
            مسیر فایل HTML تولید شده یا None
        """
        try:
            file1_path = case.get("file1")
            file2_path = case.get("file2")

            if not file1_path or not file2_path:
                return None

            with open(
                file1_path, "r", encoding="utf-8", errors="ignore"
            ) as f:
                lines1 = f.readlines()

            with open(
                file2_path, "r", encoding="utf-8", errors="ignore"
            ) as f:
                lines2 = f.readlines()

            html_diff = HtmlDiff(tabsize=4, wrapcolumn=80)
            html_content = html_diff.make_file(
                lines1,
                lines2,
                fromdesc=f"Student: {case['student1']}",
                todesc=f"Student: {case['student2']}",
                context=True,
                numlines=3,
            )

            html_filename = (
                f"Q{case['question']}_"
                f"{case['student1']}_vs_{case['student2']}.html"
            )
            html_path = os.path.join(self.html_reports_dir, html_filename)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return html_path

        except Exception as e:
            print(f"  [WARN] خطا در تولید HTML diff: {str(e)}")
            return None

    def generate_html_reports(self, plagiarism_cases: List[Dict]) -> int:
        """
        تولید گزارش‌های HTML برای تمام موارد تقلب

        Returns:
            تعداد فایل‌های HTML تولید شده
        """
        generated_count = 0

        print("\n[INFO] در حال تولید گزارش‌های HTML...")

        for case in plagiarism_cases:
            html_path = self.generate_html_diff(case)
            if html_path:
                case["html_report"] = html_path
                generated_count += 1

        print(f"  [+] {generated_count} فایل HTML تولید شد")
        return generated_count

    def generate_csv_report(
        self, plagiarism_cases: List[Dict], statistics: Dict = None
    ) -> bool:
        """
        تولید فایل گزارش CSV

        Args:
            plagiarism_cases: لیست موارد تقلب
            statistics: آمار تقلب (برای خوشه‌ها)
        """
        try:
            sorted_cases = sorted(
                plagiarism_cases,
                key=lambda x: (x["question"], -x["similarity"]),
            )

            with open(
                self.report_file,
                "w",
                newline="",
                encoding=config.Config.REPORT_ENCODING,
            ) as csvfile:
                fieldnames = [
                    "Question",
                    "Student 1",
                    "Student 2",
                    "Similarity %",
                    "HTML Report",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for case in sorted_cases:
                    html_report = case.get("html_report", "")
                    if html_report:
                        html_report = os.path.relpath(
                            html_report, config.Config.OUTPUT_DIR
                        )

                    writer.writerow(
                        {
                            "Question": f"Q{case['question']}",
                            "Student 1": case["student1"],
                            "Student 2": case["student2"],
                            "Similarity %": f"{case['similarity']:.2f}",
                            "HTML Report": html_report,
                        }
                    )

            print(f"\n[+] فایل گزارش CSV ذخیره شد: {self.report_file}")

            # گزارش خوشه‌ها
            if statistics and statistics.get("clusters"):
                clusters_file = os.path.join(
                    config.Config.OUTPUT_DIR, "Clusters_Report.csv"
                )
                with open(
                    clusters_file,
                    "w",
                    newline="",
                    encoding=config.Config.REPORT_ENCODING,
                ) as csvfile:
                    fieldnames = ["Cluster ID", "Size", "Students"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for cluster in statistics["clusters"]:
                        writer.writerow(
                            {
                                "Cluster ID": (
                                    f"Cluster #{cluster['cluster_id']}"
                                ),
                                "Size": cluster["size"],
                                "Students": ", ".join(cluster["students"]),
                            }
                        )

                print(
                    f"[+] فایل گزارش خوشه‌ها ذخیره شد: {clusters_file}"
                )

            return True

        except Exception as e:
            print(f"\n[ERROR] خطا در تولید فایل CSV: {str(e)}")
            return False

    def generate_all_reports(
        self, plagiarism_cases: List[Dict], statistics: Dict
    ):
        """
        تولید تمام گزارش‌ها
        """
        print("\n" + "=" * 60)
        print("[STEP 4] مرحله تولید گزارش")
        print("=" * 60)

        self.print_console_summary(plagiarism_cases, statistics)
        self.generate_html_reports(plagiarism_cases)
        self.generate_csv_report(plagiarism_cases, statistics)
        self.generate_detailed_report(plagiarism_cases, statistics)


def write_log_file(log_entries: List[Dict]):
    """
    نوشتن فایل لاگ
    """
    log_file = config.Config.get_log_file_path()

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("فایل لاگ MasterGrader\n")
            f.write("=" * 80 + "\n")
            f.write(
                f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            if not log_entries:
                f.write("[+] هیچ خطایی رخ نداد.\n")
            else:
                f.write(
                    f"[WARN] تعداد خطاها: {len(log_entries)}\n\n"
                )

                for entry in log_entries:
                    f.write(
                        f"خطا: {entry.get('message', 'نامشخص')}\n"
                    )
                    if entry.get("student_id"):
                        f.write(f"  دانشجو: {entry['student_id']}\n")
                    if entry.get("file_path"):
                        f.write(f"  فایل: {entry['file_path']}\n")
                    f.write("\n")

        print(f"[+] فایل لاگ ذخیره شد: {log_file}")

    except Exception as e:
        print(f"[ERROR] خطا در نوشتن فایل لاگ: {str(e)}")