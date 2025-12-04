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
            print(f"  [WARN] {error_info.get('message', 'خطا')}")
            if error_info.get('student_id'):
                print(f"     دانشجو: {error_info['student_id']}")
            if error_info.get('file_path'):
                print(f"     فایل: {error_info['file_path']}")

    def validate_environment(self) -> bool:
        """
        اعتبارسنجی محیط و تنظیمات

        Returns:
            True اگر همه چیز معتبر باشد
        """
        print("=" * 80)
        print("MasterGrader - سیستم جامع تصحیح و تشخیص تقلب")
        print("=" * 80)
        print("\n[INFO] در حال بررسی تنظیمات...")

        # بررسی تنظیمات
        errors = config.Config.validate_config()
        if errors:
            print("\n[-] خطاهای تنظیمات:")
            for error in errors:
                print(f"  • {error}")
            return False

        print("[+] تنظیمات معتبر است")

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
        print("[STEP 1] استخراج بازگشتی فایل‌های ZIP (Sandbox)")
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
                f"\n[+] استخراج کامل شد: {len(self.temp_dirs)} پوشه موقت ایجاد شد"
            )
            print(
                f"[+] تعداد دانشجویان پردازش شده: {len(self.extraction_results)}"
            )

            return True

        except Exception as e:
            print(f"\n[-] خطا در مرحله استخراج: {str(e)}")
            return False

    def step2_organization(self) -> bool:
        """
        مرحله 2: سازماندهی و نگاشت فایل‌ها

        Returns:
            True اگر موفق بود
        """
        print("\n" + "=" * 80)
        print("[STEP 2] سازماندهی و نگاشت هوشمند فایل‌ها")
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
                f"\n[+] سازماندهی کامل شد: {total_organized} فایل سازماندهی شد"
            )
            print(
                f"[+] تعداد دانشجویان سازماندهی شده: {len(self.organization_results)}"
            )

            return True

        except Exception as e:
            print(f"\n[-] خطا در مرحله سازماندهی: {str(e)}")
            return False

    def step3_plagiarism_detection(self) -> bool:
        """
        مرحله 3: تشخیص تقلب

        Returns:
            True اگر موفق بود
        """
        print("\n" + "=" * 80)
        print("[STEP 3] تشخیص تقلب با الگوریتم توکن‌سازی")
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
                f"\n[+] تشخیص تقلب کامل شد: {len(self.plagiarism_cases)} مورد شناسایی شد"
            )

            return True

        except Exception as e:
            print(f"\n[-] خطا در مرحله تشخیص تقلب: {str(e)}")
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
            print(f"\n[-] خطا در مرحله گزارش‌دهی: {str(e)}")
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
                "\n[WARN] مرحله استخراج با خطا مواجه شد، اما ادامه می‌دهیم..."
            )

        # مرحله 2: سازماندهی
        if not self.step2_organization():
            print(
                "\n[-] خطا: مرحله سازماندهی ضروری است. برنامه متوقف می‌شود."
            )
            return False

        # مرحله 3: تشخیص تقلب
        if not self.step3_plagiarism_detection():
            print("\n[WARN] مرحله تشخیص تقلب با خطا مواجه شد.")

        # مرحله 4: گزارش‌دهی
        if not self.step4_reporting():
            print("\n[WARN] مرحله گزارش‌دهی با خطا مواجه شد.")

        # خلاصه نهایی
        self.print_final_summary()

        # پاکسازی پوشه‌های موقت
        self.cleanup_temp_dirs()

        return True

    def cleanup_temp_dirs(self):
        """پاکسازی پوشه‌های موقت"""
        print(
            f"\n[INFO] در حال پاکسازی {len(self.temp_dirs)} پوشه موقت..."
        )
        for temp_dir in self.temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    # در صورت خطا در پاکسازی پوشه موقت، آن را نادیده می‌گیریم
                    pass
        print("[+] پاکسازی کامل شد")

    def print_final_summary(self):
        """چاپ خلاصه نهایی"""
        print("\n" + "=" * 80)
        print("[DONE] فرآیند کامل شد!")
        print("=" * 80)
        print(f"\n[SUMMARY] خلاصه:")
        print(
            f"  • دانشجویان پردازش شده: {len(self.extraction_results)}"
        )
        print(
            "  • فایل‌های سازماندهی شده: "
            f"{sum(r.get('total_files', 0) for r in self.organization_results.values())}"
        )
        print(
            f"  • موارد تقلب شناسایی شده: {len(self.plagiarism_cases)}"
        )
        print(f"  • خطاها: {len(self.log_entries)}")
        print(f"\n[OUTPUT] فایل‌های خروجی:")
        print(
            f"  • پوشه فایل‌های سازماندهی شده: {config.Config.OUTPUT_DIR}"
        )
        print(
            f"  • گزارش CSV: {config.Config.get_report_file_path()}"
        )
        print(
            "  • گزارش تفصیلی: "
            f"{os.path.join(config.Config.OUTPUT_DIR, 'Detailed_Report.txt')}"
        )
        print(
            f"  • فایل لاگ: {config.Config.get_log_file_path()}"
        )
        print("\n" + "=" * 80)


def parse_arguments():
    """پارس کردن آرگومان‌های خط فرمان"""
    parser = argparse.ArgumentParser(
        description=(
            "MasterGrader - سیستم جامع تصحیح و تشخیص تقلب تمرینات C"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
مثال‌ها:
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
        help=f"مسیر پوشه ورودی دانشجویان (پیش‌فرض: {config.Config.ROOT_DIR})",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"مسیر پوشه خروجی (پیش‌فرض: {config.Config.OUTPUT_DIR})",
    )

    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=None,
        help=(
            "آستانه شباهت برای تشخیص تقلب (درصد، پیش‌فرض: "
            f"{config.Config.SIMILARITY_THRESHOLD})"
        ),
    )

    parser.add_argument(
        "--template",
        "-T",
        type=str,
        default=None,
        help="مسیر فایل کد قالب (برای حذف کدهای آماده استاد)",
    )

    parser.add_argument(
        "--questions",
        "-q",
        type=int,
        default=None,
        help=f"تعداد سوالات (پیش‌فرض: {config.Config.NUM_QUESTIONS})",
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
            print("\n[+] برنامه با موفقیت به پایان رسید!")
            return 0
        else:
            print(
                "\n[WARN] برنامه با خطا به پایان رسید. لطفاً لاگ‌ها را بررسی کنید."
            )
            return 1

    except KeyboardInterrupt:
        print("\n\n[WARN] برنامه توسط کاربر متوقف شد.")
        return 1
    except Exception as e:
        print(f"\n[-] خطای غیرمنتظره: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())