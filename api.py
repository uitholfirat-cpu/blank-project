from __future__ import annotations

import os
import shutil
import tempfile
import uuid
import zipfile
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Tuple
import sys

from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from main import MasterGrader


# Ensure stdout is line-buffered so that print logs flush immediately,
# even when running under Uvicorn/PyInstaller.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        # If reconfiguration is not supported, fall back to default buffering.
        pass


class QuestionId(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    Q5 = "Q5"
    Q6 = "Q6"


class PlagiarismCaseModel(BaseModel):
    id: str
    questionId: QuestionId
    studentA: str
    studentB: str
    similarity: float
    # Keep these as required fields so the JSON shape matches the frontend mock data exactly.
    # When data is missing we return empty strings from the builder functions.
    clusterId: str
    codeA: str
    codeB: str


class DashboardStats(BaseModel):
    totalStudents: int
    totalQuestions: int
    highRiskCases: int
    averageSimilarity: float


class GradeDistributionItem(BaseModel):
    questionId: QuestionId
    submissions: int
    highRisk: int


class OriginalityStatItem(BaseModel):
    label: str
    value: float


class UploadResponse(BaseModel):
    plagiarismCases: List[PlagiarismCaseModel]
    dashboardStats: DashboardStats
    gradeDistribution: List[GradeDistributionItem]
    originalityStats: List[OriginalityStatItem]
    processingErrors: List[str] = []
    reportFiles: Dict[str, str] = {}


class GradingSettings(BaseModel):
    threshold: Optional[float] = None
    ignore_comments: Optional[bool] = None
    ignore_variable_names: Optional[bool] = None
    normalize_whitespace: Optional[bool] = None
    tokenization_enabled: Optional[bool] = None
    
    # Advanced sensitivity settings (برای شخصی‌سازی پیشرفته)
    sensitivity_mode: Optional[str] = None  # "smart", "balanced", "strict", "custom"
    ignore_function_names: Optional[bool] = None
    ignore_type_names: Optional[bool] = None
    ignore_string_literals: Optional[bool] = None
    ignore_numeric_literals: Optional[bool] = None
    ignore_operator_spacing: Optional[bool] = None
    ignore_bracket_style: Optional[bool] = None


class SubmissionValidationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class GradingEngineError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


app = FastAPI(title="MasterGrader API", version="1.0.0")

# Allow the Next.js dev server and local desktop app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4321",
        "http://127.0.0.1:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the statically exported Next.js frontend (from the `out` directory) at the root path.
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "out")

# Directory where generated report files are persisted for download via the API.
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.exception_handler(404)
async def custom_404_handler(request, exc):
    detail = getattr(exc, "detail", "Not Found")
    return {"detail": detail}


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    threshold: Optional[float] = Query(None),
    ignore_comments: Optional[bool] = Query(None),
    ignore_variable_names: Optional[bool] = Query(None),
    normalize_whitespace: Optional[bool] = Query(None),
    tokenization_enabled: Optional[bool] = Query(None),
) -> UploadResponse:
    print("DEBUG: Upload request received!", flush=True)

    settings = GradingSettings(
        threshold=threshold,
        ignore_comments=ignore_comments,
        ignore_variable_names=ignore_variable_names,
        normalize_whitespace=normalize_whitespace,
        tokenization_enabled=tokenization_enabled,
    )

    try:
        return process_submission_batch(
            file_stream=file.file,
            filename=file.filename or "submissions.zip",
            settings=settings,
        )
    except SubmissionValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_submission", "message": exc.message},
        ) from exc
    except GradingEngineError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "grading_failed", "message": exc.message},
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": str(exc)},
        ) from exc


def _snapshot_config() -> Dict[str, Any]:
    return {
        "ROOT_DIR": config.Config.ROOT_DIR,
        "OUTPUT_DIR": config.Config.OUTPUT_DIR,
        "SIMILARITY_THRESHOLD": config.Config.SIMILARITY_THRESHOLD,
        "TOKENIZATION_ENABLED": config.Config.TOKENIZATION_ENABLED,
        "NORMALIZE_WHITESPACE": config.Config.NORMALIZE_WHITESPACE,
        "REMOVE_COMMENTS": config.Config.REMOVE_COMMENTS,
        "REMOVE_INCLUDES": config.Config.REMOVE_INCLUDES,
        "IGNORE_VARIABLES": config.Config.IGNORE_VARIABLES,
    }


def _restore_config(snapshot: Dict[str, Any]) -> None:
    config.Config.ROOT_DIR = snapshot["ROOT_DIR"]
    config.Config.OUTPUT_DIR = snapshot["OUTPUT_DIR"]
    config.Config.SIMILARITY_THRESHOLD = snapshot["SIMILARITY_THRESHOLD"]
    config.Config.TOKENIZATION_ENABLED = snapshot["TOKENIZATION_ENABLED"]
    config.Config.NORMALIZE_WHITESPACE = snapshot["NORMALIZE_WHITESPACE"]
    config.Config.REMOVE_COMMENTS = snapshot["REMOVE_COMMENTS"]
    config.Config.REMOVE_INCLUDES = snapshot["REMOVE_INCLUDES"]
    config.Config.IGNORE_VARIABLES = snapshot["IGNORE_VARIABLES"]


def _apply_settings_from_request(settings: GradingSettings) -> None:
    """
    اعمال تنظیمات سطح درخواست روی Config سراسری.

    توجه: آستانه تشخیص (threshold) همچنان اینجا ست می‌شود تا با
    MasterGrader همگام باشد. تنظیمات دیگری مانند حذف کامنت‌ها و
    نادیده‌گرفتن نام متغیرها علاوه بر این، به صورت مستقیم به MasterGrader
    نیز پاس داده می‌شوند تا رفتار موتور در هر درخواست شفاف باشد.
    """
    if settings.threshold is not None:
        config.Config.SIMILARITY_THRESHOLD = settings.threshold
    if settings.ignore_comments is not None:
        config.Config.REMOVE_COMMENTS = settings.ignore_comments
    if settings.ignore_variable_names is not None:
        config.Config.IGNORE_VARIABLES = settings.ignore_variable_names
    if settings.normalize_whitespace is not None:
        config.Config.NORMALIZE_WHITESPACE = settings.normalize_whitespace
    if settings.tokenization_enabled is not None:
        config.Config.TOKENIZATION_ENABLED = settings.tokenization_enabled


def process_submission_batch(
    file_stream: BinaryIO,
    filename: str,
    settings: GradingSettings,
) -> UploadResponse:
    safe_name = os.path.basename(filename) or "submissions.zip"

    if not safe_name.lower().endswith(".zip"):
        raise SubmissionValidationError("Only .zip files are supported.")

    batch_id = uuid.uuid4().hex

    with tempfile.TemporaryDirectory(prefix="mastergrader_") as work_dir:
        upload_path = os.path.join(work_dir, safe_name)

        # Save uploaded file to disk
        try:
            try:
                file_stream.seek(0)
            except Exception:
                # Not all streams are seekable; ignore if seeking fails
                pass

            with open(upload_path, "wb") as buffer:
                shutil.copyfileobj(file_stream, buffer)
        except Exception as exc:
            raise SubmissionValidationError(f"Failed to save uploaded file: {exc}") from exc

        root_dir = os.path.join(work_dir, "root")
        os.makedirs(root_dir, exist_ok=True)

        # Extract the uploaded ZIP to a temporary root directory
        try:
            with zipfile.ZipFile(upload_path, "r") as zf:
                if not zf.infolist():
                    raise SubmissionValidationError("Uploaded zip archive is empty.")
                zf.extractall(root_dir)
        except SubmissionValidationError:
            raise
        except zipfile.BadZipFile as exc:
            raise SubmissionValidationError(f"Uploaded file is not a valid zip archive: {exc}") from exc
        except Exception as exc:
            raise SubmissionValidationError(f"Failed to extract uploaded archive: {exc}") from exc

        # If the archive contains a single top-level directory, treat that as ROOT_DIR
        try:
            entries = [os.path.join(root_dir, name) for name in os.listdir(root_dir)]
            top_dirs = [p for p in entries if os.path.isdir(p)]
            top_files = [p for p in entries if os.path.isfile(p)]
            if len(top_dirs) == 1 and not top_files:
                root_dir = top_dirs[0]
        except Exception:
            # If anything goes wrong here, fall back to using the original root_dir
            pass

        # Ensure there is at least some content after extraction
        if not any(os.scandir(root_dir)):
            raise SubmissionValidationError("No files found after extracting archive.")

        # Use a per-request output directory; MasterGrader will populate this
        output_dir = os.path.join(work_dir, "organized")
        os.makedirs(output_dir, exist_ok=True)

        snapshot = _snapshot_config()
        try:
            _apply_settings_from_request(settings)

            grader = MasterGrader(
                root_dir=root_dir,
                output_dir=output_dir,
                threshold=config.Config.SIMILARITY_THRESHOLD,
                template_path=config.Config.TEMPLATE_CODE_PATH,
                ignore_comments=settings.ignore_comments,
                ignore_variable_names=settings.ignore_variable_names,
                normalize_whitespace=settings.normalize_whitespace,
                tokenization_enabled=settings.tokenization_enabled,
            )

            try:
                success = grader.run()
            except Exception as exc:
                raise GradingEngineError(f"Grading engine raised an error: {exc}") from exc

            if not success:
                raise GradingEngineError("Grading engine reported failure for this batch.")

            # Build JSON response matching the frontend's expected data structure
            plagiarism_cases = _build_plagiarism_cases(grader)
            dashboard_stats = _build_dashboard_stats(grader, plagiarism_cases)
            grade_distribution = _build_grade_distribution(grader, plagiarism_cases)
            originality_stats = _build_originality_stats(grader, plagiarism_cases)

            processing_errors = _build_processing_errors(grader.log_entries)
            report_files = _persist_report_files(batch_id)

            return UploadResponse(
                plagiarismCases=plagiarism_cases,
                dashboardStats=dashboard_stats,
                gradeDistribution=grade_distribution,
                originalityStats=originality_stats,
                processingErrors=processing_errors,
                reportFiles=report_files,
            )
        finally:
            _restore_config(snapshot)


def _read_code_file(path: Optional[str]) -> str:
    if not path or not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _build_cluster_map(statistics: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
    """
    Build a mapping from (student1, student2) pair to a clusterId string.
    """
    clusters = statistics.get("clusters") or []
    pair_to_cluster: Dict[Tuple[str, str], str] = {}

    for cluster in clusters:
        students = cluster.get("students") or []
        cluster_id = cluster.get("cluster_id")
        if not students or cluster_id is None:
            continue

        label = f"cluster-{cluster_id}"
        sorted_students = sorted(students)
        for i in range(len(sorted_students)):
            for j in range(i + 1, len(sorted_students)):
                key = (sorted_students[i], sorted_students[j])
                pair_to_cluster[key] = label

    return pair_to_cluster


def _build_plagiarism_cases(grader: MasterGrader) -> List[PlagiarismCaseModel]:
    raw_cases = grader.plagiarism_cases or []
    statistics = grader.statistics or {}
    pair_to_cluster = _build_cluster_map(statistics)

    cases: List[PlagiarismCaseModel] = []

    for idx, case in enumerate(raw_cases):
        question_num = case.get("question")
        student1 = case.get("student1", "")
        student2 = case.get("student2", "")
        similarity = float(case.get("similarity", 0.0))

        question_id = QuestionId(f"Q{question_num}") if question_num in range(1, config.Config.NUM_QUESTIONS + 1) else QuestionId.Q1
        file1 = case.get("file1")
        file2 = case.get("file2")

        code_a = _read_code_file(file1)
        code_b = _read_code_file(file2)

        key = tuple(sorted((student1, student2)))
        cluster_id = pair_to_cluster.get(key) or f"cluster-{question_id.value.lower()}"

        case_id = f"case-{question_id.value.lower()}-{idx + 1}"

        cases.append(
            PlagiarismCaseModel(
                id=case_id,
                questionId=question_id,
                studentA=student1,
                studentB=student2,
                similarity=similarity,
                clusterId=cluster_id,
                codeA=code_a,
                codeB=code_b,
            )
        )

    return cases


def _build_dashboard_stats(
    grader: MasterGrader,
    cases: List[PlagiarismCaseModel],
) -> DashboardStats:
    total_students = len(grader.extraction_results or {})
    total_questions = config.Config.NUM_QUESTIONS
    threshold = config.Config.SIMILARITY_THRESHOLD

    high_risk_cases = sum(1 for c in cases if c.similarity >= threshold)
    if cases:
        avg_similarity = sum(c.similarity for c in cases) / len(cases)
    else:
        avg_similarity = 0.0

    return DashboardStats(
        totalStudents=total_students,
        totalQuestions=total_questions,
        highRiskCases=high_risk_cases,
        averageSimilarity=avg_similarity,
    )


def _build_grade_distribution(
    grader: MasterGrader,
    cases: List[PlagiarismCaseModel],
) -> List[GradeDistributionItem]:
    distribution: List[GradeDistributionItem] = []
    threshold = config.Config.SIMILARITY_THRESHOLD

    organization_results = grader.organization_results or {}

    for q_num in range(1, config.Config.NUM_QUESTIONS + 1):
        question_id = QuestionId(f"Q{q_num}")

        submissions = 0
        for student_result in organization_results.values():
            mapped_files = student_result.get("mapped_files") or {}
            if q_num in mapped_files:
                submissions += 1

        high_risk = sum(
            1 for c in cases if c.questionId == question_id and c.similarity >= threshold
        )

        distribution.append(
            GradeDistributionItem(
                questionId=question_id,
                submissions=submissions,
                highRisk=high_risk,
            )
        )

    return distribution


def _build_originality_stats(
    grader: MasterGrader,
    cases: List[PlagiarismCaseModel],
) -> List[OriginalityStatItem]:
    total_students = len(grader.extraction_results or {})
    threshold = config.Config.SIMILARITY_THRESHOLD

    suspicious_students = set()
    for c in cases:
        if c.similarity >= threshold:
            suspicious_students.add(c.studentA)
            suspicious_students.add(c.studentB)

    if total_students > 0:
        suspicious_percent = round(100.0 * len(suspicious_students) / total_students)
    else:
        suspicious_percent = 0.0

    original_percent = max(0.0, 100.0 - suspicious_percent)

    return [
        OriginalityStatItem(label="Original", value=original_percent),
        OriginalityStatItem(label="Suspicious", value=suspicious_percent),
    ]


def _build_processing_errors(log_entries: List[Dict[str, Any]]) -> List[str]:
    """
    Convert internal log entries into a user-facing list of warning strings.
    """
    errors: List[str] = []
    seen: set[str] = set()

    for entry in log_entries or []:
        message = str(entry.get("message", "")).strip()
        student_id = str(entry.get("student_id") or "").strip()
        file_path = str(entry.get("file_path") or "").strip()

        parts: List[str] = []
        if message:
            parts.append(message)

        detail_parts: List[str] = []
        if student_id:
            detail_parts.append(f"student {student_id}")
        if file_path:
            detail_parts.append(file_path)

        if detail_parts:
            parts.append(f"({' – '.join(detail_parts)})")

        text = " ".join(parts).strip()
        if not text:
            continue
        if text in seen:
            continue

        seen.add(text)
        errors.append(text)

    return errors


def _persist_report_files(batch_id: str) -> Dict[str, str]:
    """
    Copy generated report files from the per-request output directory into a
    persistent reports folder and return API download paths.
    """
    files: Dict[str, str] = {}

    # Main CSV report
    csv_src = config.Config.get_report_file_path()
    if os.path.exists(csv_src):
        csv_name = f"{batch_id}_Plagiarism_Report.csv"
        csv_dest = os.path.join(REPORTS_DIR, csv_name)
        shutil.copy2(csv_src, csv_dest)
        files["csv"] = f"/download/{csv_name}"

    # Detailed text report
    detailed_src = os.path.join(config.Config.OUTPUT_DIR, "Detailed_Report.txt")
    if os.path.exists(detailed_src):
        detailed_name = f"{batch_id}_Detailed_Report.txt"
        detailed_dest = os.path.join(REPORTS_DIR, detailed_name)
        shutil.copy2(detailed_src, detailed_dest)
        files["detailed"] = f"/download/{detailed_name}"

    # Clusters CSV report
    clusters_src = os.path.join(config.Config.OUTPUT_DIR, "Clusters_Report.csv")
    if os.path.exists(clusters_src):
        clusters_name = f"{batch_id}_Clusters_Report.csv"
        clusters_dest = os.path.join(REPORTS_DIR, clusters_name)
        shutil.copy2(clusters_src, clusters_dest)
        files["clusters"] = f"/download/{clusters_name}"

    return files


@app.get("/download/{filename}")
async def download_report(filename: str):
    """
    Serve generated report files for download by the frontend.
    """
    safe_name = os.path.basename(filename)
    file_path = os.path.join(REPORTS_DIR, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found.")

    return FileResponse(path=file_path, filename=safe_name)


if os.path.isdir(FRONTEND_BUILD_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="frontend")
