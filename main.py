"""
MasterGrader - سیستم جامع تصحیح و تشخیص تقلب تمرینات C
این برنامه تمام مراحل استخراج، سازماندهی و تشخیص تقلب را به صورت خودکار انجام می‌دهد.
"""

import os
import sys
import argparse
import shutil
from typing import List, Dict

import config
import extractor
import file_mapper
import plagiarism_detector
import reporter


class MasterGrader:
    """کلاس اصلی هماهنگ‌کننده تمام ماژول‌ها"""

    def __init__(
        self,
        root_dir: str = None,
        output_dir: str = None,
        threshold: float = None,
        template_path: str = None,
    ):
        """
        Args:
            root_dir: مسیر ورودی (پیش‌فرض از config)
            output_dir: مسیر خروجی (پیش‌فرض از config)
            threshold: آستانه شباهت (پیش‌فرض از config)
            template_path: مسیر فایل قالب (پیش‌فرض از config)
        """
        self.log_entries: List[Dict] = []
        self.extraction_results: Dict = {}
        self.organization_results: Dict = {}
        self.plagiarism_cases: List[Dict] = []
        self.statistics: Dict = {}
        self.temp_dirs: List[str] = []  # لیست پوشه‌های موقت برای پاکسازی

        # اعمال تنظیمات CLI
        if root_dir:
            config.Config.ROOT_DIR = root_dir
        if output_dir:
            config.Config.OUTPUT_DIR = output_dir
        if threshold is not None:
            config.Config.SIMILARITY_THRESHOLD = threshold
        if template_path:
            config.Config.TEMPLATE_CODE_PATH = template_path

    def log_error(self, error_info: Dict):
        """
        ثبت خطا در لاگ

        Args:
            error_info: اطلاعات خطا
        """
        self.log_entries.append(error_info)
        if config.Config.DETAILED_LOGGING:
            print(f"  [WARN] {error_info.get('message', 'Error')}")
            if error_info.get('student_id'):
                print(f"     Student: {error_info['student_id']}")
            if error_info.get('file_path'):
                print(f"     File: {error_info['file_path']}")

    def validate_environment(self) -> bool:
        """
        اعتبارسنجی محیط و تنظیمات

        Returns:
            True اگر همه چیز معتبر باشد
        """
        print("=" * 80)
        print("MasterGrader - Automated C assignment grading and plagiarism detection")
        print("=" * 80)
        print("\n[INFO] Checking configuration...")

        # بررسی تنظیمات
        errors = config.Config.validate_config()
        if errors:
            print("\n[ERROR] Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("[+] Configuration is valid")

        # ایجاد پوشه‌های مورد نیاز
        config.Config.initialize_directories()

        return True

    def step1_extraction(self) -> bool:
        """
        مرحله 1: استخراج فایل‌های ZIP

        Returns:
            True اگر موفق بود
        """
        print("\n" + "=" * 80)
        print("[STEP 1] Recursive extraction of ZIP archives (sandbox)")
        print("=" * 80)

        try:
            self.extraction_results = extractor.extract_student_submissions(
                config.Config.ROOT_DIR,
                log_callback=self.log_error,
            )

            # جمع‌آوری پوشه‌های موقت برای پاکسازی بعدی
            for result in self.extraction_results.values():
                temp_path = result.get("temp_path")
                if temp_path:
                    self.temp_dirs.append(temp_path)

            print(
                f"\n[+] Extraction completed: {len(self.temp_dirs)} temporary folders created"
            )
            print(
                f"[+] Number of processed students: {len(self.extraction_results)}"
            )

            return True

        except Exception as e:
            print(f"\n[ERROR] Extraction step failed: {str(e)}")
            return False

    def step2_organization(self) -> bool:
        """
        مرحله 2: سازماندهی و نگاشت فایل‌ها

        Returns:
            True اگر موفق بود
        """
        print("\n" + "=" * 80)
        print("[STEP 2] Organizing and mapping files")
        print("=" * 80)

        try:
            # استفاده از نتایج استخراج (پوشه‌های موقت)
            self.organization_results = file_mapper.organize_all_students(
                self.extraction_results,
                config.Config.OUTPUT_DIR,
            )

            total_organized = sum(
                result.get("total_files", 0)
                for result in self.organization_results.values()
            )

            print(
                f"\n[+] Organization completed: {total_organized} files organized"
            )
            print(
                f"[+] Number of students organized: {len(self.organization_results)}"
            )

            return True

        except Exception as e:
            print(f"\n[ERROR] Organization step failed: {str(e)}")
            return False

    def step3_plagiarism_detection(self) -> bool:
        """
        مرحله 3: تشخیص تقلب

        Returns:
            True اگر موفق بود
        """
        print("\n" + "=" * 80)
        print("[STEP 3] Plagiarism detection using tokenization")
        print("=" * 80)

        try:
            (
                self.plagiarism_cases,
                self.statistics,
            ) = plagiarism_detector.detect_plagiarism(
                config.Config.OUTPUT_DIR,
                template_path=config.Config.TEMPLATE_CODE_PATH,
            )

            print(
                f"\n[+] Plagiarism detection completed: {len(self.plagiarism_cases)} cases detected"
            )

            return True

        except Exception as e:
            print(f"\n[ERROR] Plagiarism detection step failed: {str(e)}")
            return False

    def step4_reporting(self) -> bool:
        """
        مرحله 4: تولید گزارش‌ها

        Returns:
            True اگر موفق بود
        """
        try:
            report_gen = reporter.Reporter()
            report_gen.generate_all_reports(
                self.plagiarism_cases, self.statistics
            )

            # نوشتن فایل لاگ
            reporter.write_log_file(self.log_entries)

            return True

        except Exception as e:
            print(f"\n[ERROR] Reporting step failed: {str(e)}")
            return False

    def run(self) -> bool:
        """
        اجرای کامل فرآیند

        Returns:
            True اگر تمام مراحل موفق بودند
        """
        # اعتبارسنجی
        if not self.validate_environment():
            return False

        # مرحله 1: استخراج
        if not self.step1_extraction():
            print(
                "\n[WARN] Extraction step failed, continuing..."
            )

        # مرحله 2: سازماندهی
        if not self.step2_organization():
            print(
                "\n[ERROR] Organization step failed. The program will stop."
            )
            return False

        # مرحله 3: تشخیص تقلب
        if not self.step3_plagiarism_detection():
            print("\n[WARN] Plagiarism detection step failed.")

        # مرحله 4: گزارش‌دهی
        if not self.step4_reporting():
            print("\n[WARN] Reporting step failed.")

        # خلاصه نهایی
        self.print_final_summary()

        # پاکسازی پوشه‌های موقت
        self.cleanup_temp_dirs()

        return True

    def cleanup_temp_dirs(self):
        """پاکسازی پوشه‌های موقت"""
        print(
            f"\n[INFO] Cleaning up {len(self.temp_dirs)} temporary folders..."
        )
        for temp_dir in self.temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    # در صورت خطا در پاکسازی پوشه موقت، آن را نادیده می‌گیریم
                    pass
        print("[+] Cleanup completed")

    def print_final_summary(self):
        """چاپ خلاصه نهایی"""
        print("\n" + "=" * 80)
        print("[DONE] Processing finished!")
        print("=" * 80)
        print("\n[SUMMARY] Summary:")
        print(
            f"  - Processed students: {len(self.extraction_results)}"
        )
        print(
            "  - Organized files: "
            f"{sum(r.get('total_files', 0) for r in self.organization_results.values())}"
        )
        print(
            f"  - Detected plagiarism cases: {len(self.plagiarism_cases)}"
        )
        print(f"  - Logged errors: {len(self.log_entries)}")
        print("\n[OUTPUT] Output files:")
        print(
            f"  - Organized submissions folder: {config.Config.OUTPUT_DIR}"
        )
        print(
            f"  - CSV report: {config.Config.get_report_file_path()}"
        )
        print(
            "  - Detailed text report: "
            f"{os.path.join(config.Config.OUTPUT_DIR, 'Detailed_Report.txt')}"
        )
        print(
            f"  - Log file: {config.Config.get_log_file_path()}"
        )
        print("\n" + "=" * 80)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "MasterGrader - Automated C assignment grading and plagiarism detection"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --input "C:/submissions" --output "C:/results"
  python main.py --input "C:/submissions" --threshold 90 --template "template.c"
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help=f"Input root folder of student submissions (default: {config.Config.ROOT_DIR})",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"Output folder (default: {config.Config.OUTPUT_DIR})",
    )

    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=None,
        help=(
            "Similarity threshold for plagiarism detection (percent, default: "
            f"{config.Config.SIMILARITY_THRESHOLD})"
        ),
    )

    parser.add_argument(
        "--template",
        "-T",
        type=str,
        default=None,
        help="Path to template C code file (to subtract instructor-provided code)",
    )

    parser.add_argument(
        "--questions",
        "-q",
        type=int,
        default=None,
        help=f"Number of questions (default: {config.Config.NUM_QUESTIONS})",
    )

    return parser.parse_args()


def main():
    """تابع اصلی"""
    try:
        # پارس کردن آرگومان‌ها
        args = parse_arguments()

        # اعمال تنظیمات اضافی
        if args.questions:
            config.Config.NUM_QUESTIONS = args.questions

        # ایجاد instance با تنظیمات CLI
        grader = MasterGrader(
            root_dir=args.input,
            output_dir=args.output,
            threshold=args.threshold,
            template_path=args.template,
        )

        success = grader.run()

        if success:
            print("\n[+] Program finished successfully.")
            return 0
        else:
            print(
                "\n[WARN] Program finished with errors. Please check the logs."
            )
            return 1

    except KeyboardInterrupt:
        print("\n\n[WARN] Program interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())