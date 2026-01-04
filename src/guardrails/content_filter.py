"""
Content filtering guardrails.

Filters harmful, inappropriate, or sensitive content from LLM outputs.
"""

from typing import List, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum
import re


class FilterCategory(str, Enum):
    """Content filter categories"""
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    SELF_HARM = "self_harm"
    PROFANITY = "profanity"
    PERSONAL_INFO = "personal_info"
    FINANCIAL_DATA = "financial_data"
    MEDICAL_DATA = "medical_data"


@dataclass
class FilterResult:
    """Result from content filtering"""
    passed: bool
    blocked_categories: List[FilterCategory]
    confidence: float
    sanitized_text: str
    details: Dict[str, Any]


class ContentFilter:
    """
    Filters harmful or sensitive content.
    
    Features:
    - Pattern-based detection
    - Category-specific filtering
    - Text sanitization
    """
    
    def __init__(self):
        # Define keyword patterns for each category
        self.patterns: Dict[FilterCategory, List[str]] = {
            FilterCategory.HATE_SPEECH: [
                r'\b(hate|racist|sexist)\b',
                # Add more patterns
            ],
            FilterCategory.VIOLENCE: [
                r'\b(kill|murder|assault|attack|harm)\b',
            ],
            FilterCategory.PROFANITY: [
                r'\b(damn|hell|crap)\b',  # Mild examples
            ],
            FilterCategory.PERSONAL_INFO: [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email
            ],
            FilterCategory.FINANCIAL_DATA: [
                r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
            ],
        }
        
        # Compile patterns
        self.compiled_patterns: Dict[FilterCategory, List[re.Pattern]] = {}
        for category, patterns in self.patterns.items():
            self.compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def filter(
        self,
        text: str,
        strict_mode: bool = False,
        allowed_categories: Set[FilterCategory] = None
    ) -> FilterResult:
        """
        Filter text for harmful content.
        
        Args:
            text: Text to filter
            strict_mode: If True, block on any match
            allowed_categories: Categories to ignore
            
        Returns:
            FilterResult
        """
        blocked = []
        details = {}
        
        for category, patterns in self.compiled_patterns.items():
            # Skip if category is allowed
            if allowed_categories and category in allowed_categories:
                continue
            
            matches = []
            for pattern in patterns:
                found = pattern.findall(text)
                if found:
                    matches.extend(found)
            
            if matches:
                blocked.append(category)
                details[category.value] = {
                    "matches": matches,
                    "count": len(matches)
                }
        
        # Sanitize text
        sanitized = self._sanitize(text, blocked)
        
        # Determine if passed
        passed = len(blocked) == 0 or (not strict_mode and self._is_minor(blocked))
        
        return FilterResult(
            passed=passed,
            blocked_categories=blocked,
            confidence=1.0 if blocked else 0.0,
            sanitized_text=sanitized,
            details=details
        )
    
    def _sanitize(self, text: str, blocked_categories: List[FilterCategory]) -> str:
        """Sanitize text by masking sensitive content"""
        sanitized = text
        
        for category in blocked_categories:
            if category == FilterCategory.PERSONAL_INFO:
                # Mask emails
                sanitized = re.sub(
                    r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',
                    '[EMAIL]',
                    sanitized,
                    flags=re.IGNORECASE
                )
                # Mask SSN
                sanitized = re.sub(
                    r'\b\d{3}-\d{2}-\d{4}\b',
                    '[SSN]',
                    sanitized
                )
            
            elif category == FilterCategory.FINANCIAL_DATA:
                # Mask credit cards
                sanitized = re.sub(
                    r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                    '[CARD]',
                    sanitized
                )
        
        return sanitized
    
    def _is_minor(self, blocked_categories: List[FilterCategory]) -> bool:
        """Check if violations are minor (e.g., only profanity)"""
        minor_categories = {FilterCategory.PROFANITY}
        return all(cat in minor_categories for cat in blocked_categories)
