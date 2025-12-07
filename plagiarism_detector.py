"""
Advanced Plagiarism Detection Engine
This module uses token stream comparison for accurate plagiarism detection
while preventing cross-question contamination.
"""

import os
from typing import List, Dict, Tuple, Optional, Literal, Set
from difflib import SequenceMatcher
from collections import defaultdict

import tokenizer
import config

TokenizationMode = Literal["structural", "literal"]

# Try to import networkx for clustering (optional)
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class PlagiarismDetector:
    """
    Forensic-grade plagiarism detector using token stream comparison.
    
    Features:
    - Token stream-based comparison (not raw text)
    - Template subtraction to remove boilerplate
    - Question-isolated comparisons (no cross-question contamination)
    - Accurate similarity scoring using SequenceMatcher
    """

    def __init__(
        self,
        template_tokens: Optional[List[str]] = None,
        mode: TokenizationMode = "structural",
    ):
        """
        Initialize the plagiarism detector.
        
        Args:
            template_tokens: Template token list (for subtraction)
            mode: Tokenization mode ("structural" or "literal")
        """
        self.tokenizer = tokenizer.CTokenizer()
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        self.template_tokens = template_tokens
        self.mode = mode

    def _calculate_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """
        Calculate similarity between two token lists using SequenceMatcher.
        
        Args:
            tokens1: First token list
            tokens2: Second token list
        
        Returns:
            Similarity percentage (0-100)
        """
        if not tokens1 or not tokens2:
            return 0.0
        
        # Create cache key (sorted for symmetry)
        cache_key = tuple(sorted([
            " ".join(tokens1),
            " ".join(tokens2)
        ]))
        
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        # Use SequenceMatcher on token lists
        # Convert to strings for SequenceMatcher (space-separated)
        token_str1 = " ".join(tokens1)
        token_str2 = " ".join(tokens2)
        
        # Calculate ratio
        similarity = SequenceMatcher(None, token_str1, token_str2).ratio()
        similarity_percent = similarity * 100.0
        
        # Cache result
        self.similarity_cache[cache_key] = similarity_percent
        
        return similarity_percent

    def _is_valid_for_comparison(
        self, file_path: str
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Check if file is valid for comparison and return its tokens.
        
        Args:
            file_path: Path to C file
        
        Returns:
            Tuple (is_valid, token_list) - token_list is None if invalid
        """
        if not os.path.exists(file_path):
            return False, None
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            
            # Tokenize to list
            student_tokens = self.tokenizer.tokenize_to_list(code, mode=self.mode)
            
            # Check minimum token count
            if len(student_tokens) < config.Config.MIN_TOKEN_COUNT:
                return False, None
            
            # Apply template subtraction if template exists
            if self.template_tokens and student_tokens:
                student_tokens = self.tokenizer.subtract_template_tokens(
                    student_tokens,
                    self.template_tokens
                )
                
                # Re-check token count after template subtraction
                if len(student_tokens) < config.Config.MIN_TOKEN_COUNT:
                    return False, None
            
            return True, student_tokens
        
        except Exception as e:
            print(f"[WARN] Error processing file {file_path}: {str(e)}")
            return False, None

    def compare_two_files(self, file1_path: str, file2_path: str) -> float:
        """
        Compare two files and calculate similarity.
        
        Args:
            file1_path: Path to first file
            file2_path: Path to second file
        
        Returns:
            Similarity percentage (0-100)
        """
        is_valid1, tokens1 = self._is_valid_for_comparison(file1_path)
        is_valid2, tokens2 = self._is_valid_for_comparison(file2_path)
        
        if not is_valid1 or not is_valid2 or not tokens1 or not tokens2:
            return 0.0
        
        return self._calculate_similarity(tokens1, tokens2)

    def detect_plagiarism_in_question(
        self, question_dir: str, question_num: int
    ) -> List[Dict]:
        """
        Detect plagiarism within a specific question directory.
        
        This ensures NO cross-question contamination - only files in
        the same question directory are compared.
        
        Args:
            question_dir: Directory containing files for this question
            question_num: Question number
        
        Returns:
            List of plagiarism cases
        """
        plagiarism_cases: List[Dict] = []
        
        if not os.path.exists(question_dir):
            return plagiarism_cases
        
        # Collect all valid student files for this question
        student_files: Dict[str, str] = {}
        for file_name in os.listdir(question_dir):
            if file_name.endswith(tuple(config.Config.ACCEPTED_EXTENSIONS)):
                student_id = os.path.splitext(file_name)[0]
                file_path = os.path.join(question_dir, file_name)
                
                is_valid, _ = self._is_valid_for_comparison(file_path)
                if is_valid:
                    student_files[student_id] = file_path
        
        if len(student_files) < 2:
            # Need at least 2 files to compare
            return plagiarism_cases
        
        # Compare all pairs of files (only within this question)
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
                    plagiarism_cases.append({
                        "question": question_num,
                        "student1": student1_id,
                        "student2": student2_id,
                        "similarity": round(similarity, 2),
                        "file1": file1_path,
                        "file2": file2_path,
                    })
                
                comparison_count += 1
                if comparison_count % 50 == 0:
                    print(
                        f"    [+] {comparison_count}/{total_comparisons} comparisons completed..."
                    )
        
        return plagiarism_cases

    def detect_plagiarism_all_questions(
        self, output_dir: str
    ) -> List[Dict]:
        """
        Detect plagiarism across all questions.
        
        Each question is processed in isolation to prevent cross-contamination.
        
        Args:
            output_dir: Output directory containing Q1, Q2, etc. folders
        
        Returns:
            List of all plagiarism cases
        """
        all_plagiarism_cases: List[Dict] = []
        
        print("\n" + "=" * 60)
        print("[STEP 3] Plagiarism detection step")
        print("=" * 60)
        
        for question_num in range(1, config.Config.NUM_QUESTIONS + 1):
            question_dir = os.path.join(output_dir, f"Q{question_num}")
            
            if os.path.exists(question_dir):
                print(f"\n[INFO] Checking question {question_num}...")
                
                # Only compare files within this question directory
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
            else:
                print(f"  [INFO] Question {question_num} directory not found, skipping...")
        
        return all_plagiarism_cases

    def find_clusters(self, plagiarism_cases: List[Dict]) -> List[Dict]:
        """
        Find plagiarism clusters using graph connectivity.
        
        Args:
            plagiarism_cases: List of plagiarism cases
        
        Returns:
            List of clusters (groups of students)
        """
        if not NETWORKX_AVAILABLE:
            return self._find_clusters_simple(plagiarism_cases)
        
        G = nx.Graph()
        
        # Add edges for each plagiarism case
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
                clusters.append({
                    "students": cluster_students,
                    "size": len(cluster_students),
                    "cluster_id": len(clusters) + 1,
                })
        
        return clusters

    def _find_clusters_simple(self, plagiarism_cases: List[Dict]) -> List[Dict]:
        """
        Find clusters without networkx (fallback implementation).
        
        Uses DFS to find connected components.
        """
        connections: Dict[str, Set[str]] = defaultdict(set)
        
        for case in plagiarism_cases:
            student1 = case["student1"]
            student2 = case["student2"]
            connections[student1].add(student2)
            connections[student2].add(student1)
        
        visited: set = set()
        clusters: List[Dict] = []
        cluster_id = 1
        
        def dfs(student: str, current_cluster: set):
            """Depth-first search to find connected students."""
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
                    clusters.append({
                        "students": sorted(list(cluster)),
                        "size": len(cluster),
                        "cluster_id": cluster_id,
                    })
                    cluster_id += 1
        
        return clusters

    def get_statistics(self, plagiarism_cases: List[Dict]) -> Dict:
        """
        Calculate plagiarism statistics.
        
        Args:
            plagiarism_cases: List of plagiarism cases
        
        Returns:
            Dictionary with statistics
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
            # Statistics by question
            stats["by_question"][case["question"]] += 1
            
            # Statistics by student
            stats["by_student"][case["student1"]] += 1
            stats["by_student"][case["student2"]] += 1
            
            # Similarity distribution
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
) -> Optional[List[str]]:
    """
    Load and tokenize template file.
    
    Args:
        template_path: Path to template file
        mode: Tokenization mode
    
    Returns:
        List of template tokens or None
    """
    if not template_path or not os.path.exists(template_path):
        return None
    
    try:
        tokenizer_instance = tokenizer.CTokenizer()
        with open(template_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        
        tokens = tokenizer_instance.tokenize_to_list(code, mode=mode)
        return tokens if tokens else None
    except Exception as e:
        print(f"[WARN] Error loading template file: {str(e)}")
        return None


def detect_plagiarism(
    output_dir: str,
    template_path: Optional[str] = None,
    mode: TokenizationMode = "structural",
) -> Tuple[List[Dict], Dict]:
    """
    Main function for plagiarism detection.
    
    Args:
        output_dir: Output directory with Q1, Q2, etc. folders
        template_path: Optional path to template file
        mode: Tokenization mode ("structural" for Smart mode, "literal" for Strict)
    
    Returns:
        Tuple of (plagiarism_cases, statistics)
    """
    # Load template tokens if provided
    template_tokens = load_template_tokens(template_path, mode=mode)
    if template_tokens:
        print(f"[+] Template file loaded: {template_path}")
        print(f"    Template contains {len(template_tokens)} tokens")
    
    # Create detector
    detector = PlagiarismDetector(
        template_tokens=template_tokens,
        mode=mode,
    )
    
    # Detect plagiarism (each question processed separately)
    plagiarism_cases = detector.detect_plagiarism_all_questions(output_dir)
    
    # Calculate statistics
    statistics = detector.get_statistics(plagiarism_cases)
    
    # Display cluster information
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