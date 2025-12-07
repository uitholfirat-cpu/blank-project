"""
Reporting module for MasterGrader.

Generates CSV, detailed text, HTML diff reports, and a log file.
"""

import csv
import os
from datetime import datetime
from difflib import HtmlDiff
from typing import Dict, List, Optional

import config


class Reporter:
    def __init__(self) -> None:
        self.report_file = config.Config.get_report_file_path()
        self.html_reports_dir = config.Config.get_html_reports_dir()
        os.makedirs(self.html_reports_dir, exist_ok=True)

    def print_console_summary(
        self,
        plagiarism_cases: List[Dict],
        statistics: Dict,
    ) -> None:
        """
        Print a concise plagiarism summary to the console.
        """
        if not config.Config.CONSOLE_OUTPUT_ENABLED:
            return

        print("\n" + "=" * 80)
        print("[SUMMARY] Plagiarism detection summary")
        print("=" * 80)

        total_cases = statistics.get("total_cases", 0)
        print("\n[STATS] Overall statistics:")
        print(f"  - Total potential plagiarism cases: {total_cases}")

        by_question = statistics.get("by_question") or {}
        if by_question:
            print("\n[STATS] Cases by question:")
            for question_num in sorted(by_question.keys()):
                count = by_question[question_num]
                print(f"  - Question {question_num}: {count} case(s)")

        similarity_dist = statistics.get("similarity_distribution") or {}
        if similarity_dist:
            print("\n[STATS] Similarity distribution:")
            for range_name, count in similarity_dist.items():
                if count > 0:
                    print(f"  - {range_name}%: {count} case(s)")

        by_student = statistics.get("by_student") or {}
        if by_student:
            print("\n[WARN] Students with the most flagged pairs:")
            sorted_students = sorted(
                by_student.items(), key=lambda x: x[1], reverse=True
            )[:10]
            for student_id, count in sorted_students:
                print(f"  - {student_id}: {count} case(s)")

        clusters = statistics.get("clusters") or {}
        if clusters:
            print("\n[INFO] Detected plagiarism clusters:")
            for cluster in clusters:
                students_str = ", ".join(cluster["students"])
                print(
                    f"  - Cluster #{cluster['cluster_id']}: "
                    f"{cluster['size']} students - [{students_str}]"
                )

        if plagiarism_cases:
            print("\n[INFO] Sample of detected cases (first 10):")
            print("-" * 80)
            print(
                f"{'Question':<8} {'Student 1':<15} "
                f"{'Student 2':<15} {'Similarity %':<12}"
            )
            print("-" * 80)

            for case in plagiarism_cases[:10]:
                print(
                    f"Q{case['question']:<7} {case['student1']:<15} "
                    f"{case['student2']:<15} {case['similarity']:.2f}%"
                )

            if len(plagiarism_cases) > 10:
                print(f"\n  ... and {len(plagiarism_cases) - 10} more case(s)")

        print("\n" + "=" * 80)

    def generate_detailed_report(
        self,
        plagiarism_cases: List[Dict],
        statistics: Dict,
    ) -> bool:
        """
        Generate a detailed text report summarizing all detected cases.
        """
        try:
            report_path = os.path.join(
                config.Config.OUTPUT_DIR,
                "Detailed_Report.txt",
            )

            with open(report_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("Detailed plagiarism report\n")
                f.write("=" * 80 + "\n")
                f.write(
                    f"Generated at: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(
                    f"Similarity threshold: "
                    f"{config.Config.SIMILARITY_THRESHOLD}%\n"
                )
                f.write(
                    f"Minimum token count: {config.Config.MIN_TOKEN_COUNT}\n"
                )
                f.write("\n" + "=" * 80 + "\n\n")

                total_cases = statistics.get("total_cases", 0)
                f.write("[STATS] Overall statistics:\n")
                f.write(
                    f"  Total potential plagiarism cases: {total_cases}\n\n"
                )

                by_question = statistics.get("by_question") or {}
                if by_question:
                    f.write("[STATS] Cases by question:\n")
                    for question_num in sorted(by_question.keys()):
                        count = by_question[question_num]
                        f.write(f"  Question {question_num}: {count} case(s)\n")
                    f.write("\n")

                clusters = statistics.get("clusters") or []
                if clusters:
                    f.write("🔗 Plagiarism clusters:\n")
                    for cluster in clusters:
                        students_str = ", ".join(cluster["students"])
                        f.write(
                            f"  Cluster #{cluster['cluster_id']}: "
                            f"{cluster['size']} students – [{students_str}]\n"
                        )
                    f.write("\n")

                if plagiarism_cases:
                    f.write("🔍 All detected cases:\n")
                    f.write("-" * 80 + "\n")

                    current_question: Optional[int] = None
                    for case in sorted(
                        plagiarism_cases,
                        key=lambda x: (x["question"], -x["similarity"]),
                    ):
                        if current_question != case["question"]:
                            current_question = case["question"]
                            f.write(f"\n📝 Question {current_question}:\n")
                            f.write("-" * 80 + "\n")

                        f.write(
                            f"  • {case['student1']} <-> {case['student2']}: "
                            f"{case['similarity']:.2f}%\n"
                        )

            print(f"[OK] Detailed text report saved: {report_path}")
            return True

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[ERROR] Error generating detailed{exc}")
            return False

    def generate_html_diff(self, case: Dict) -> Optional[str]:
        """
        Generate an HTML side-by-side diff for a single plagiarism case.
        """
        try:
            file1_path = case.get("file1")
            file2_path = case.get("file2")

            if not file1_path or not file2_path:
                return None

            with open(file1_path, "r", encoding="utf-8", errors="ignore") as f:
                lines1 = f.readlines()

            with open(file2_path, "r", encoding="utf-8", errors="ignore") as f:
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
                f"Q{case['question']}_{case['student1']}_vs_{case['student2']}.html"
            )
            html_path = os.path.join(self.html_reports_dir, html_filename)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return html_path

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"  ⚠ Error generating HTML diff: {exc}")
            return None

    def generate_html_reports(self, plagiarism_cases: List[Dict]) -> int:
        """
        Generate HTML diff reports for all detected cases.
        """
        generated_count = 0

        print("\n[STEP] Generating HTML diff reports...")

        for case in plagiarism_cases:
            html_path = self.generate_html_diff(case)
            if html_path:
                case["html_report"] = html_path
                generated_count += 1

        print(f"  [OK] {generated_count} HTML file(s) generated")
        return generated_count

    def generate_csv_report(
        self,
        plagiarism_cases: List[Dict],
        statistics: Optional[Dict] = None,
    ) -> bool:
        """
        Generate the main CSV report and an optional clusters CSV.
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

            print(f"\n[OK] CSV plagiarism report saved: {self.report_file}")

            if statistics and statistics.get("clusters"):
                clusters_file = os.path.join(
                    config.Config.OUTPUT_DIR,
                    "Clusters_Report.csv",
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
                                "Cluster ID": f"Cluster #{cluster['cluster_id']}",
                                "Size": cluster["size"],
                                "Students": ", ".join(cluster["students"]),
                            }
                        )

                print(f"[OK] Cluster report saved: {clusters_file}")

            return True

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"\n[ERROR] Error generating CSV report: {exc}")
            return False

    def generate_all_reports(
        self,
        plagiarism_cases: List[Dict],
        statistics: Dict,
    ) -> None:
        """
        Run the full reporting pipeline: console summary, HTML, CSV, and text.
        """
        print("\n" + "=" * 60)
        print("[STEP] Generating reports")
        print("=" * 60)

        self.print_console_summary(plagiarism_cases, statistics)
        self.generate_html_reports(plagiarism_cases)
        self.generate_csv_report(plagiarism_cases, statistics)
        self.generate_detailed_report(plagiarism_cases, statistics)


def write_log_file(log_entries: List[Dict]) -> None:
    """
    Write a human-readable log file summarizing extraction/processing issues.
    """
    log_file = config.Config.get_log_file_path()

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("MasterGrader log file\n")
            f.write("=" * 80 + "\n")
            f.write(
                f"Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            if not log_entries:
                f.write("No errors were recorded.\n")
            else:
                f.write(f"Number of errors: {len(log_entries)}\n\n")

                for entry in log_entries:
                    message = entry.get("message", "Unknown error")
                    student_id = entry.get("student_id")
                    file_path = entry.get("file_path")

                    f.write(f"Error: {message}\n")
                    if student_id:
                        f.write(f"  Student: {student_id}\n")
                    if file_path:
                        f.write(f"  File: {file_path}\n")
                    f.write("\n")

        print(f"[ Log file saved: {log_file}")

    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"✗ Error writing log file: {exc}")