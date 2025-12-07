"""
Robust File Mapping Module for Question Identification
This module uses strict regex-based heuristics to accurately map files to questions
without cross-question contamination.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

import config

# Configure logging
logger = logging.getLogger(__name__)


class FileMapper:
    """
    Forensic-grade file mapper that prevents cross-question contamination.
    
    Uses strict regex patterns that are non-ambiguous and will skip files
    rather than making incorrect guesses.
    """

    def __init__(self):
        """Initialize the file mapper with strict patterns."""
        self.mapping_patterns = self._build_strict_patterns()
        self.warnings: List[str] = []

    def _build_strict_patterns(self) -> Dict[int, List[re.Pattern]]:
        """
        Build strict, non-ambiguous regex patterns for each question.
        
        Each pattern is designed to match ONLY that specific question number
        and will not accidentally match other questions.
        
        Returns:
            Dictionary mapping question_number -> list of regex patterns
        """
        patterns: Dict[int, List[re.Pattern]] = {}
        
        for q_num in range(1, config.Config.NUM_QUESTIONS + 1):
            question_patterns: List[re.Pattern] = []
            
            # Pattern 1: Direct question markers (q1, question1, soal1, etc.)
            # Must be word boundaries to prevent matching q10 when looking for q1
            question_patterns.append(
                re.compile(rf"\bq{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bquestion{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bsoal{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bsual{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bproblem{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bex{q_num}\b", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\bexercise{q_num}\b", re.IGNORECASE)
            )
            
            # Pattern 2: Filename patterns (q1.c, question1.c, 1.c, 01.c)
            # Must match at start of filename or after separator
            ext_pattern = '|'.join([re.escape(ext) for ext in config.Config.ACCEPTED_EXTENSIONS])
            question_patterns.append(
                re.compile(
                    rf"(?:^|[/\\])q{q_num}(?:\.(?:{ext_pattern})|[/\\_]|$)",
                    re.IGNORECASE
                )
            )
            question_patterns.append(
                re.compile(
                    rf"(?:^|[/\\])question{q_num}(?:\.(?:{ext_pattern})|[/\\_]|$)",
                    re.IGNORECASE
                )
            )
            # Standalone number at start (with extension or separator)
            # Use negative lookbehind/lookahead to avoid matching multi-digit numbers
            if q_num < 10:
                # For single digits, ensure we don't match part of a larger number
                question_patterns.append(
                    re.compile(
                        rf"(?:^|[/\\])(?:0?{q_num})(?:\.(?:{ext_pattern})|[/\\_]|$)",
                        re.IGNORECASE
                    )
                )
            else:
                # For multi-digit, match exactly
                question_patterns.append(
                    re.compile(
                        rf"(?:^|[/\\]){q_num}(?:\.(?:{ext_pattern})|[/\\_]|$)",
                        re.IGNORECASE
                    )
                )
            
            # Pattern 3: Bracket/parenthesis patterns ([1].c, (1).c, _1_.c)
            question_patterns.append(
                re.compile(rf"\[{q_num}\]", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"\({q_num}\)", re.IGNORECASE)
            )
            question_patterns.append(
                re.compile(rf"_{q_num}_", re.IGNORECASE)
            )
            
            # Pattern 4: Directory patterns (folder name containing question number)
            # Must be a directory name, not part of a filename
            question_patterns.append(
                re.compile(rf"[/\\](?:q|question|soal|problem|ex|exercise)?{q_num}[/\\]", re.IGNORECASE)
            )
            
            patterns[q_num] = question_patterns
        
        return patterns

    def _extract_all_numbers(self, text: str) -> List[int]:
        """
        Extract all numbers from text that could be question numbers.
        
        Returns:
            List of integers that are in valid question number range
        """
        numbers = re.findall(r'\d+', text)
        valid_numbers = []
        for num_str in numbers:
            try:
                num = int(num_str)
                if 1 <= num <= config.Config.NUM_QUESTIONS:
                    valid_numbers.append(num)
            except ValueError:
                continue
        return valid_numbers

    def _match_strict_patterns(self, file_path: str, file_name: str) -> Optional[Tuple[int, float]]:
        """
        Match file against strict patterns and return question number with confidence.
        
        Returns:
            Tuple of (question_number, confidence_score) or None if no match
        """
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/')
        
        # Track all matches with confidence scores
        matches: Dict[int, List[float]] = {}
        
        for q_num, patterns in self.mapping_patterns.items():
            confidence_scores = []
            
            for pattern in patterns:
                # Check filename
                if pattern.search(file_name):
                    confidence_scores.append(0.9)
                
                # Check full path
                if pattern.search(normalized_path):
                    confidence_scores.append(0.7)
                
                # Check directory names in path
                path_parts = normalized_path.split('/')
                for part in path_parts[:-1]:  # Exclude filename
                    if pattern.search(part):
                        confidence_scores.append(0.5)
            
            if confidence_scores:
                # Use maximum confidence for this question
                matches[q_num] = confidence_scores
        
        if not matches:
            return None
        
        # If multiple questions matched, we have an ambiguity
        if len(matches) > 1:
            matched_questions = sorted(matches.keys())
            warning_msg = (
                f"Ambiguous file mapping: '{file_name}' matches multiple questions: "
                f"{matched_questions}. Skipping to prevent cross-contamination."
            )
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
            return None
        
        # Single unambiguous match
        q_num = list(matches.keys())[0]
        confidence = max(matches[q_num])
        return (q_num, confidence)

    def map_file_to_question(self, file_path: str) -> Optional[Tuple[int, float]]:
        """
        Map a single file to a question number with strict validation.
        
        Returns:
            Tuple (question_number, confidence_score) or None if ambiguous/invalid
        """
        if not os.path.exists(file_path):
            return None
        
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # Check file extension
        if file_ext not in config.Config.ACCEPTED_EXTENSIONS:
            return None
        
        # Try strict pattern matching first
        result = self._match_strict_patterns(file_path, file_name)
        if result:
            return result
        
        # Fallback: Check if there's exactly one valid number in the filename/path
        # This is safer than extracting random numbers
        all_text = f"{file_path} {file_name}"
        valid_numbers = self._extract_all_numbers(all_text)
        
        # Only proceed if we have exactly ONE valid question number
        if len(valid_numbers) == 1:
            q_num = valid_numbers[0]
            # Low confidence fallback
            return (q_num, 0.4)
        elif len(valid_numbers) > 1:
            # Multiple numbers found - too ambiguous
            warning_msg = (
                f"Ambiguous file: '{file_name}' contains multiple question numbers: "
                f"{valid_numbers}. Skipping to prevent cross-contamination."
            )
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
            return None
        
        # No match found
        return None

    def map_student_files(
        self, student_dir: str, student_id: str
    ) -> Dict[int, List[str]]:
        """
        Map all files for a student to their respective questions.
        
        Returns:
            Dictionary {question_number: [list of file paths]}
        """
        mapping: Dict[int, List[Tuple[str, float]]] = {}
        unmapped_files: List[str] = []
        self.warnings.clear()
        
        if not os.path.exists(student_dir):
            logger.warning(f"Student directory does not exist: {student_dir}")
            return {}
        
        # Collect all C source files
        c_files: List[str] = []
        for root, dirs, files in os.walk(student_dir):
            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs
                if not any(ignore in d.lower() for ignore in config.Config.IGNORE_PATTERNS)
            ]
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_ext = os.path.splitext(file_name)[1].lower()
                
                if file_ext in config.Config.ACCEPTED_EXTENSIONS:
                    c_files.append(file_path)
        
        if not c_files:
            logger.warning(
                f"No C source files found in directory for student {student_id}: {student_dir}"
            )
            return {}
        
        # Map each file to a question
        for file_path in c_files:
            result = self.map_file_to_question(file_path)
            
            if result:
                question_num, confidence = result
                if question_num not in mapping:
                    mapping[question_num] = []
                mapping[question_num].append((file_path, confidence))
            else:
                unmapped_files.append(file_path)
        
        # Log warnings for unmapped files
        if unmapped_files:
            logger.info(
                f"Student {student_id}: {len(unmapped_files)} file(s) could not be mapped "
                f"to questions: {[os.path.basename(f) for f in unmapped_files]}"
            )
        
        # For each question, select the file with highest confidence
        # If multiple files match the same question, prefer higher confidence
        final_mapping: Dict[int, List[str]] = {}
        for question_num, candidates in mapping.items():
            if not candidates:
                continue
            
            # Sort by confidence (descending) and file path length (ascending)
            # Prefer shorter paths (likely closer to root)
            candidates.sort(key=lambda x: (-x[1], len(x[0])))
            
            # Only take the best match per question
            best_file = candidates[0][0]
            final_mapping[question_num] = [best_file]
            
            # Warn if multiple files matched the same question
            if len(candidates) > 1:
                logger.warning(
                    f"Student {student_id}, Q{question_num}: Multiple files matched. "
                    f"Selected '{os.path.basename(best_file)}' (confidence: {candidates[0][1]:.2f}). "
                    f"Other candidates: {[os.path.basename(f[0]) for f in candidates[1:]]}"
                )
        
        return final_mapping

    def organize_student_files(
        self, student_dir: str, student_id: str, output_dir: str
    ) -> Dict:
        """
        Organize student files into question-specific directories.
        
        Returns:
            Dictionary with organization results
        """
        import shutil
        
        mapping = self.map_student_files(student_dir, student_id)
        
        # Collect all C files for reporting
        all_c_files: List[str] = []
        for root, dirs, files in os.walk(student_dir):
            dirs[:] = [
                d for d in dirs
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
        
        unmapped_files = [f for f in all_c_files if f not in mapped_file_paths]
        
        organized: Dict = {
            "student_id": student_id,
            "mapped_files": {},
            "unmapped_files": unmapped_files,
            "total_files": 0,
        }
        
        # Copy mapped files to organized structure
        for question_num, file_paths in mapping.items():
            if not file_paths:
                continue
            
            source_file = file_paths[0]  # Use the best match
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
                error_msg = f"Error copying file {source_file}: {str(e)}"
                logger.error(error_msg)
                organized.setdefault("errors", []).append(error_msg)
        
        return organized


def organize_all_students(
    extraction_results: Dict, output_dir: str
) -> Dict:
    """
    Organize files for all students from extraction results.
    
    Args:
        extraction_results: Results from extractor including temp_path
        output_dir: Output directory path
    
    Returns:
        Dictionary with organization results for all students
    """
    mapper = FileMapper()
    results: Dict[str, Dict] = {}
    
    print("\n" + "=" * 60)
    print("[STEP 2] File organization step")
    print("=" * 60)
    
    for student_id, extraction_data in extraction_results.items():
        temp_path = extraction_data.get("temp_path")
        
        if not temp_path or not os.path.exists(temp_path):
            logger.warning(f"Student {student_id}: temporary folder does not exist")
            results[student_id] = {
                "student_id": student_id,
                "mapped_files": {},
                "unmapped_files": [],
                "total_files": 0,
            }
            continue
        
        print(f"\n[INFO] Processing {student_id}...")
        print(f"  [INFO] Temporary folder path: {temp_path}")
        
        organized = mapper.organize_student_files(
            temp_path, student_id, output_dir
        )
        results[student_id] = organized
        
        mapped_count = len(organized["mapped_files"])
        print(f"  [+] {mapped_count} files organized")
        
        if organized.get("unmapped_files"):
            print(
                f"  [WARN] {len(organized['unmapped_files'])} files were not mapped"
            )
        
        # Print warnings if any
        if mapper.warnings:
            for warning in mapper.warnings[:3]:  # Limit to first 3 warnings
                print(f"  [WARN] {warning}")
    
    return results