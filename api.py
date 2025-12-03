from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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


app = FastAPI(title="MasterGrader API", version="1.0.0")

# Allow the Next.js dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported.")

    work_dir = tempfile.mkdtemp(prefix="mastergrader_")
    upload_path = os.path.join(work_dir, file.filename)

    # Save the uploaded file to disk
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}") from exc

    # Extract the uploaded ZIP to a temporary root directory
    root_dir = os.path.join(work_dir, "root")
    os.makedirs(root_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(upload_path, "r") as zf:
            zf.extractall(root_dir)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail=f"Uploaded file is not a valid zip: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to extract zip: {exc}") from exc

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

    # Use a per-request output directory; MasterGrader will populate this
    output_dir = os.path.join(work_dir, "organized")
    os.makedirs(output_dir, exist_ok=True)

    # Configure MasterGrader to use our temporary paths
    grader = MasterGrader(
        root_dir=root_dir,
        output_dir=output_dir,
        threshold=config.Config.SIMILARITY_THRESHOLD,
        template_path=config.Config.TEMPLATE_CODE_PATH,
    )

    success = grader.run()
    if not success:
        raise HTTPException(status_code=500, detail="MasterGrader failed to process the submissions.")

    # Build JSON response matching the frontend's mock-data structure
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