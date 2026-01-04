"""
Validators for LLM outputs and prompts.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re
import json


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result from validation"""
    passed: bool
    level: ValidationLevel
    message: str
    fixes: Optional[Dict[str, Any]] = None


class PIIDetector:
    """Detects personally identifiable information"""
    
    PII_PATTERNS = {
        "email": r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }
    
    def detect(self, text: str) -> ValidationResult:
        """Detect PII in text"""
        found_pii = {}
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_pii[pii_type] = matches
        
        if found_pii:
            return ValidationResult(
                passed=False,
                level=ValidationLevel.CRITICAL,
                message=f"PII detected: {', '.join(found_pii.keys())}",
                fixes={"remove_pii": True, "pii_types": list(found_pii.keys())}
            )
        
        return ValidationResult(
            passed=True,
            level=ValidationLevel.INFO,
            message="No PII detected"
        )


class PromptInjectionDetector:
    """Detects prompt injection attempts"""
    
    INJECTION_PATTERNS = [
        r'ignore (previous|above) (instructions|prompts)',
        r'disregard (previous|above)',
        r'forget (everything|all)',
        r'new (instructions|task|prompt)',
        r'system:?\s*you are now',
        r'act as (if|though)',
    ]
    
    def detect(self, text: str) -> ValidationResult:
        """Detect prompt injection"""
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Potential prompt injection detected: {pattern}",
                    fixes={"block_request": True}
                )
        
        return ValidationResult(
            passed=True,
            level=ValidationLevel.INFO,
            message="No prompt injection detected"
        )


class OutputValidator:
    """
    Validates LLM outputs for safety and correctness.
    
    Features:
    - PII detection
    - Prompt injection detection
    - Format validation
    - Length validation
    """
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.injection_detector = PromptInjectionDetector()
    
    def validate_output(
        self,
        output: str,
        expected_format: Optional[str] = None,
        max_length: Optional[int] = None,
        check_pii: bool = True
    ) -> List[ValidationResult]:
        """
        Validate LLM output.
        
        Args:
            output: LLM output text
            expected_format: Expected format (json, yaml, etc.)
            max_length: Maximum allowed length
            check_pii: Check for PII
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check PII
        if check_pii:
            pii_result = self.pii_detector.detect(output)
            results.append(pii_result)
        
        # Check length
        if max_length and len(output) > max_length:
            results.append(ValidationResult(
                passed=False,
                level=ValidationLevel.WARNING,
                message=f"Output exceeds max length ({len(output)} > {max_length})",
                fixes={"truncate": max_length}
            ))
        
        # Check format
        if expected_format == "json":
            try:
                json.loads(output)
                results.append(ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="Valid JSON format"
                ))
            except json.JSONDecodeError as e:
                results.append(ValidationResult(
                    passed=False,
                    level=ValidationLevel.ERROR,
                    message=f"Invalid JSON: {str(e)}",
                    fixes={"fix_json": True}
                ))
        
        return results
    
    def validate_prompt(self, prompt: str) -> List[ValidationResult]:
        """
        Validate user prompt before sending to LLM.
        
        Args:
            prompt: User prompt
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check for prompt injection
        injection_result = self.injection_detector.detect(prompt)
        results.append(injection_result)
        
        # Check for excessive length
        if len(prompt) > 10000:
            results.append(ValidationResult(
                passed=False,
                level=ValidationLevel.WARNING,
                message=f"Prompt very long ({len(prompt)} chars)",
                fixes={"truncate": 10000}
            ))
        
        return results
