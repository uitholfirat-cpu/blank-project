from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from enum import Enum
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from fastapi import FastAPI, File, HTTPException, UploadFile, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exception_handlers import http_exception_handler as fastapi_http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

import config
from main import MasterGrader


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


class GradingSettings(BaseModel):
    threshold: Optional[float] = None
    ignore_comments: Optional[bool] = None
    normalize_whitespace: Optional[bool] = None
    tokenization_enabled: Optional[bool] = None


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

# Paths for the statically exported Next.js frontend
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), "out")
FRONTEND_BUILD_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "_next")
FRONTEND_INDEX_FILE = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Serve the statically exported Next.js frontend (from the `out` directory)
if os.path.isdir(FRONTEND_BUILD_DIR):
    if os.path.isdir(FRONTEND_BUILD_STATIC_DIR):
        app.mount(
            "/_next",
            StaticFiles(directory=FRONTEND_BUILD_STATIC_DIR),
            name="next_static",
        )
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_BUILD_DIR, html=True),
        name="frontend",
    )


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    """
    For unknown non-API routes, return index.html so that the client-side
    router can handle the path. API routes still get the normal 404.
    """
    if exc.status_code == 404 and os.path.exists(FRONTEND_INDEX_FILE):
        path = request.url.path
        # Preserve JSON 404s for API and docs endpoints
        if not (
            path.startswith("/upload")
            or path.startswith("/health")
            or path.startswith("/docs")
            or path.startswith("/openapi")
        ):
            return FileResponse(FRONTEND_INDEX_FILE)

    return await fastapi_http_exception_handler(request, exc)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    threshold: Optional[float] = Query(None),
    ignore_comments: Optional[bool] = Query(None),
    normalize_whitespace: Optional[bool] = Query(None),
    tokenization_enabled: Optional[bool] = Query(None),
) -> UploadResponse:
    settings = GradingSettings(
        threshold=threshold,
        ignore_comments=ignore_comments,
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
    }


def _restore_config(snapshot: Dict[str, Any]) -> None:
    config.Config.ROOT_DIR = snapshot["ROOT_DIR"]
    config.Config.OUTPUT_DIR = snapshot["OUTPUT_DIR"]
    config.Config.SIMILARITY_THRESHOLD = snapshot["SIMILARITY_THRESHOLD"]
    config.Config.TOKENIZATION_ENABLED = snapshot["TOKENIZATION_ENABLED"]
    config.Config.NORMALIZE_WHITESPACE = snapshot["NORMALIZE_WHITESPACE"]
    config.Config.REMOVE_COMMENTS = snapshot["REMOVE_COMMENTS"]
    config.Config.REMOVE_INCLUDES = snapshot["REMOVE_INCLUDES"]


def _apply_settings_from_request(settings: GradingSettings) -> None:
    if settings.threshold is not None:
        config.Config.SIMILARITY_THRESHOLD = settings.threshold
    if settings.ignore_comments is not None:
        config.Config.REMOVE_COMMENTS = settings.ignore_comments
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

            return UploadResponse(
                plagiarismCases=plagiarism_cases,
                dashboardStats=dashboard_stats,
                gradeDistribution=grade_distribution,
                originalityStats=originality_stats,
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
