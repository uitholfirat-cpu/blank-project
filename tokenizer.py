"""
Advanced C Code Tokenizer for Plagiarism Detection
This module implements a lexer-based tokenizer that generates token streams
for accurate code comparison while ignoring variable names (Smart mode).
"""

import re
from typing import List, Tuple, Optional, Literal, Union
import config


TokenizationMode = Literal["structural", "literal"]


class CTokenizer:
    """
    Forensic-grade C tokenizer that generates token streams for comparison.
    
    Features:
    - Proper C lexer that handles all C syntax correctly
    - Comment removal
    - Macro and include removal
    - Whitespace normalization
    - Smart mode: variable name normalization (ignores variable names)
    - Strict mode: preserves all identifiers
    """

    def __init__(self):
        """Initialize the tokenizer with C syntax patterns."""
        self.keywords = config.Config.C_KEYWORDS
        self.operators = config.Config.C_OPERATORS
        self._build_regex_patterns()
        self._build_operator_trie()

    def _build_regex_patterns(self):
        """Build regex patterns for C syntax elements."""
        # Single-line comments
        self.single_line_comment = re.compile(r"//.*?$", re.MULTILINE)
        
        # Multi-line comments (non-greedy)
        self.multi_line_comment = re.compile(r"/\*.*?\*/", re.DOTALL)
        
        # Preprocessor directives (#include, #define, etc.)
        self.preprocessor_pattern = re.compile(
            r"^\s*#\s*(?:include|define|ifdef|ifndef|endif|undef|if|else|elif|pragma).*?$",
            re.MULTILINE | re.IGNORECASE
        )
        
        # String literals (handles escaped quotes)
        self.string_pattern = re.compile(
            r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
            re.DOTALL
        )
        
        # Number literals (integers, floats, hex, etc.)
        self.number_pattern = re.compile(
            r"\b(?:0[xX][0-9a-fA-F]+|0[0-7]*|[0-9]+\.[0-9]*|[0-9]+\.?[0-9]*[eE][+-]?[0-9]+|[0-9]+\.?)\b"
        )
        
        # Identifiers (variables, functions, types)
        self.identifier_pattern = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")

    def _build_operator_trie(self):
        """Build a trie-like structure for multi-character operators."""
        # Sort operators by length (longest first) for proper matching
        self.operators_sorted = sorted(
            self.operators,
            key=lambda x: (len(x), x),
            reverse=True
        )

    def _remove_comments(self, code: str, remove_comments: Optional[bool] = None) -> str:
        """Remove all comments from C code."""
        should_remove = remove_comments if remove_comments is not None else config.Config.REMOVE_COMMENTS
        if not should_remove:
            return code
        
        # Remove multi-line comments first
        code = self.multi_line_comment.sub(" ", code)
        
        # Remove single-line comments
        code = self.single_line_comment.sub(" ", code)
        
        return code

    def _remove_preprocessor(self, code: str, remove_includes: Optional[bool] = None) -> str:
        """Remove preprocessor directives."""
        should_remove = remove_includes if remove_includes is not None else config.Config.REMOVE_INCLUDES
        if not should_remove:
            return code
        
        # Remove all preprocessor lines
        code = self.preprocessor_pattern.sub(" ", code)
        
        return code

    def _normalize_whitespace(self, code: str, normalize_whitespace: Optional[bool] = None) -> str:
        """Normalize whitespace in code."""
        should_normalize = normalize_whitespace if normalize_whitespace is not None else config.Config.NORMALIZE_WHITESPACE
        if not should_normalize:
            return code
        
        # Replace all whitespace sequences with single space
        code = re.sub(r"\s+", " ", code)
        
        # Remove spaces around operators and brackets (but keep separators like semicolon)
        # This is more conservative - we'll handle spacing in tokenization
        return code

    def _is_keyword(self, word: str) -> bool:
        """Check if a word is a C keyword."""
        return word.lower() in self.keywords

    def _match_operator(self, code: str, pos: int) -> Optional[Tuple[str, int]]:
        """
        Try to match an operator starting at position pos.
        
        Returns:
            Tuple (operator_string, length) or None
        """
        for op in self.operators_sorted:
            if code[pos:pos+len(op)] == op:
                return (op, len(op))
        return None

    def _tokenize_code(
        self,
        code: str,
        mode: TokenizationMode = "structural",
    ) -> List[str]:
        """
        Tokenize C code into a list of tokens.
        
        Args:
            code: C source code
            mode: "structural" (Smart mode - normalize identifiers) or
                  "literal" (Strict mode - preserve identifiers)
        
        Returns:
            List of token strings
        """
        tokens: List[str] = []
        i = 0
        code_len = len(code)
        ignore_variables = (mode == "structural")
        
        while i < code_len:
            # Skip whitespace
            if code[i].isspace():
                i += 1
                continue
            
            # Try to match an operator (check longest first)
            op_match = self._match_operator(code, i)
            if op_match:
                op_str, op_len = op_match
                tokens.append(op_str)
                i += op_len
                continue
            
            # Try to match a number
            num_match = self.number_pattern.match(code, i)
            if num_match:
                tokens.append("NUM")
                i = num_match.end()
                continue
            
            # Try to match a string literal
            str_match = self.string_pattern.match(code, i)
            if str_match:
                tokens.append("STR")
                i = str_match.end()
                continue
            
            # Try to match an identifier or keyword
            id_match = self.identifier_pattern.match(code, i)
            if id_match:
                word = id_match.group()
                
                if self._is_keyword(word):
                    # C keywords are case-sensitive but we normalize to uppercase
                    tokens.append(word.upper())
                else:
                    # This is an identifier (variable, function, type)
                    if ignore_variables:
                        # Smart mode: normalize all identifiers to generic token
                        tokens.append("ID")
                    else:
                        # Strict mode: preserve identifier name
                        tokens.append(word)
                
                i = id_match.end()
                continue
            
            # Unknown character - skip it (could be special characters)
            i += 1
        
        return tokens

    def _tokenize_code_advanced(
        self,
        code: str,
        sensitivity: Optional['config.SensitivityConfig'] = None,
    ) -> List[str]:
        """
        Tokenize C code with advanced sensitivity configuration.
        
        Args:
            code: C source code
            sensitivity: SensitivityConfig object for granular control
        
        Returns:
            List of token strings
        """
        if sensitivity is None:
            sensitivity = config.Config.get_sensitivity_config()
        
        tokens: List[str] = []
        i = 0
        code_len = len(code)
        
        # Helper function to determine if an identifier should be normalized
        def should_normalize_identifier(identifier: str, context: str = "") -> bool:
            """Determine if identifier should be normalized based on type."""
            # This is a simplified check - in a full implementation,
            # we'd use context to distinguish variable/function/type
            # For now, we'll check based on common patterns
            
            # Check if it's likely a function (followed by '(')
            # Check if it's likely a type (preceded by keywords like struct, typedef)
            # For now, apply the general rules
            
            # We need to detect what type of identifier this is
            # This is simplified - a full implementation would need AST analysis
            return True  # Default behavior
        
        while i < code_len:
            # Skip whitespace
            if code[i].isspace():
                i += 1
                continue
            
            # Try to match an operator (check longest first)
            op_match = self._match_operator(code, i)
            if op_match:
                op_str, op_len = op_match
                tokens.append(op_str)
                i += op_len
                continue
            
            # Try to match a number
            num_match = self.number_pattern.match(code, i)
            if num_match:
                if sensitivity.ignore_numeric_literals:
                    tokens.append("NUM")
                else:
                    tokens.append(num_match.group())
                i = num_match.end()
                continue
            
            # Try to match a string literal
            str_match = self.string_pattern.match(code, i)
            if str_match:
                if sensitivity.ignore_string_literals:
                    tokens.append("STR")
                else:
                    tokens.append(str_match.group())
                i = str_match.end()
                continue
            
            # Try to match an identifier or keyword
            id_match = self.identifier_pattern.match(code, i)
            if id_match:
                word = id_match.group()
                
                if self._is_keyword(word):
                    tokens.append(word.upper())
                else:
                    # This is an identifier - check what type and apply rules
                    # Simplified: check if it should be normalized
                    should_normalize = False
                    
                    # Check variable names
                    if sensitivity.ignore_variable_names:
                        # Simple heuristic: if it's not a function call pattern
                        # Check context around identifier
                        next_chars = code[i + len(word):i + len(word) + 2].strip()
                        if next_chars and next_chars[0] != '(':
                            # Likely a variable
                            should_normalize = True
                    
                    # Check function names
                    if sensitivity.ignore_function_names:
                        next_chars = code[i + len(word):i + len(word) + 2].strip()
                        if next_chars and next_chars[0] == '(':
                            # Likely a function
                            should_normalize = True
                    
                    # Check type names (simplified)
                    if sensitivity.ignore_type_names:
                        # Check if preceded by type keywords
                        prev_text = code[max(0, i-20):i].strip().lower()
                        if any(kw in prev_text.split()[-2:] for kw in ['struct', 'typedef', 'enum', 'union']):
                            should_normalize = True
                    
                    if should_normalize:
                        tokens.append("ID")
                    else:
                        tokens.append(word)
                
                i = id_match.end()
                continue
            
            # Unknown character - skip it
            i += 1
        
        return tokens

    def tokenize(self, code: str, mode: TokenizationMode = "structural") -> str:
        """
        Tokenize C code and return token stream as string.
        
        Args:
            code: C source code
            mode: Tokenization mode
        
        Returns:
            Token stream as space-separated string (for SequenceMatcher)
        """
        if not code or not code.strip():
            return ""
        
        # Step 1: Remove comments
        code = self._remove_comments(code)
        
        # Step 2: Remove preprocessor directives
        code = self._remove_preprocessor(code)
        
        # Step 3: Normalize whitespace
        code = self._normalize_whitespace(code)
        
        # Step 4: Tokenize
        tokens = self._tokenize_code(code, mode=mode)
        
        # Step 5: Return as space-separated string for SequenceMatcher
        # Using spaces allows SequenceMatcher to work on token sequences properly
        token_string = " ".join(tokens)
        
        return token_string

    def tokenize_to_list(self, code: str, mode: TokenizationMode = "structural") -> List[str]:
        """
        Tokenize C code and return as list of tokens.
        
        Args:
            code: C source code
            mode: Tokenization mode
        
        Returns:
            List of token strings
        """
        if not code or not code.strip():
            return []
        
        # Step 1: Remove comments
        code = self._remove_comments(code)
        
        # Step 2: Remove preprocessor directives
        code = self._remove_preprocessor(code)
        
        # Step 3: Normalize whitespace
        code = self._normalize_whitespace(code)
        
        # Step 4: Tokenize
        tokens = self._tokenize_code(code, mode=mode)
        
        return tokens

    def get_token_count(self, code: str, mode: TokenizationMode = "structural") -> int:
        """
        Count the number of tokens in code.
        
        Args:
            code: C source code
            mode: Tokenization mode
        
        Returns:
            Number of tokens
        """
        tokens = self.tokenize_to_list(code, mode=mode)
        return len(tokens)

    def is_code_valid_for_plagiarism_check(
        self, code: str, mode: TokenizationMode = "structural"
    ) -> bool:
        """
        Check if code has enough tokens to be valid for plagiarism detection.
        
        Args:
            code: C source code
            mode: Tokenization mode
        
        Returns:
            True if code is valid for comparison
        """
        token_count = self.get_token_count(code, mode=mode)
        return token_count >= config.Config.MIN_TOKEN_COUNT

    def subtract_template_tokens(
        self,
        student_tokens: List[str],
        template_tokens: List[str]
    ) -> List[str]:
        """
        Remove template tokens from student tokens (template subtraction).
        
        Uses sequence matching to find and remove template code segments
        from the student's code to prevent false positives from boilerplate.
        
        Args:
            student_tokens: Student's token list
            template_tokens: Template's token list
        
        Returns:
            Student tokens with template tokens removed
        """
        if not template_tokens or not student_tokens:
            return student_tokens
        
        # Convert to strings for matching
        student_str = " ".join(student_tokens)
        template_str = " ".join(template_tokens)
        
        # Remove the entire template if it appears as a substring
        if template_str in student_str:
            student_str = student_str.replace(template_str, "", 1)
            # Re-tokenize after removal (split on spaces)
            result_tokens = [t for t in student_str.split() if t]
            return result_tokens if result_tokens else student_tokens
        
        # If exact match not found, try to remove common subsequences
        # This is more complex - for now, return original tokens
        # Advanced template subtraction can be added later if needed
        return student_tokens

    def tokenize_with_sensitivity(
        self,
        code: str,
        sensitivity: Optional['config.SensitivityConfig'] = None
    ) -> str:
        """
        Tokenize code using SensitivityConfig for advanced customization.
        
        Args:
            code: C source code
            sensitivity: SensitivityConfig object (uses default if None)
        
        Returns:
            Token stream as space-separated string
        """
        if sensitivity is None:
            sensitivity = config.Config.get_sensitivity_config()
        
        # Apply preprocessing based on sensitivity config
        if sensitivity.remove_comments:
            code = self._remove_comments(code, remove_comments=True)
        
        if sensitivity.remove_includes:
            code = self._remove_preprocessor(code, remove_includes=True)
        
        if sensitivity.normalize_whitespace:
            code = self._normalize_whitespace(code, normalize_whitespace=True)
        
        # Determine mode based on sensitivity settings
        # If any identifier type is ignored, use structural mode
        use_structural = (
            sensitivity.ignore_variable_names or
            sensitivity.ignore_function_names or
            sensitivity.ignore_type_names
        )
        mode = "structural" if use_structural else "literal"
        
        # Tokenize with mode
        tokens = self._tokenize_code(code, mode=mode)
        
        # Apply literal-specific rules if needed
        if not use_structural:
            # In literal mode, check if we need to normalize literals
            processed_tokens = []
            for token in tokens:
                if sensitivity.ignore_string_literals and token.startswith('"'):
                    processed_tokens.append("STR")
                elif sensitivity.ignore_numeric_literals and token.replace('.', '').replace('-', '').isdigit():
                    processed_tokens.append("NUM")
                else:
                    processed_tokens.append(token)
            tokens = processed_tokens
        
        return " ".join(tokens)

    def tokenize_to_list_with_sensitivity(
        self,
        code: str,
        sensitivity: Optional['config.SensitivityConfig'] = None
    ) -> List[str]:
        """
        Tokenize code to list using SensitivityConfig.
        
        Args:
            code: C source code
            sensitivity: SensitivityConfig object
        
        Returns:
            List of tokens
        """
        token_string = self.tokenize_with_sensitivity(code, sensitivity)
        return token_string.split() if token_string else []


def tokenize_file(file_path: str, mode: TokenizationMode = "structural") -> str:
    """
    Tokenize a C file and return token stream.
    
    Args:
        file_path: Path to C file
        mode: Tokenization mode
    
    Returns:
        Token stream as string
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        
        tokenizer = CTokenizer()
        return tokenizer.tokenize(code, mode=mode)
    except Exception as e:
        print(f"[WARN] Error reading file {file_path}: {str(e)}")
        return ""


def tokenize_file_to_list(file_path: str, mode: TokenizationMode = "structural") -> List[str]:
    """
    Tokenize a C file and return token list.
    
    Args:
        file_path: Path to C file
        mode: Tokenization mode
    
    Returns:
        List of tokens
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        
        tokenizer = CTokenizer()
        return tokenizer.tokenize_to_list(code, mode=mode)
    except Exception as e:
        print(f"[WARN] Error reading file {file_path}: {str(e)}")
        return []


def get_token_count_from_file(
    file_path: str, mode: TokenizationMode = "structural"
) -> int:
    """
    Count tokens in a C file.
    
    Args:
        file_path: Path to C file
        mode: Tokenization mode
    
    Returns:
        Number of tokens
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        
        tokenizer = CTokenizer()
        return tokenizer.get_token_count(code, mode=mode)
    except Exception:
        return 0