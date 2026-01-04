"""
Safety scoring for LLM outputs.
"""

from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(str, Enum):
    """Safety levels"""
    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"
    BLOCKED = "blocked"


@dataclass
class SafetyScore:
    """Overall safety score"""
    level: SafetyLevel
    score: float  # 0-1, higher is safer
    categories: Dict[str, float]  # Category scores
    recommendations: list


class SafetyScorer:
    """
    Scores content for overall safety.
    
    Aggregates results from filters and validators.
    """
    
    def score(
        self,
        text: str,
        filter_result: Any = None,
        validation_results: list = None
    ) -> SafetyScore:
        """
        Calculate safety score.
        
        Args:
            text: Text to score
            filter_result: Content filter result
            validation_results: Validation results
            
        Returns:
            SafetyScore
        """
        scores = {}
        recommendations = []
        
        # Base score
        base_score = 1.0
        
        # Factor in filter results
        if filter_result:
            if not filter_result.passed:
                base_score *= 0.5
                scores["content_filter"] = 0.5
                recommendations.append(
                    f"Content blocked: {', '.join(c.value for c in filter_result.blocked_categories)}"
                )
            else:
                scores["content_filter"] = 1.0
        
        # Factor in validation results
        if validation_results:
            critical_count = sum(1 for r in validation_results if not r.passed and r.level.value == "critical")
            error_count = sum(1 for r in validation_results if not r.passed and r.level.value == "error")
            warning_count = sum(1 for r in validation_results if not r.passed and r.level.value == "warning")
            
            if critical_count > 0:
                base_score *= 0.3
                scores["validation"] = 0.3
                recommendations.append(f"{critical_count} critical validation failures")
            elif error_count > 0:
                base_score *= 0.6
                scores["validation"] = 0.6
                recommendations.append(f"{error_count} validation errors")
            elif warning_count > 0:
                base_score *= 0.8
                scores["validation"] = 0.8
            else:
                scores["validation"] = 1.0
        
        # Determine safety level
        if base_score >= 0.9:
            level = SafetyLevel.SAFE
        elif base_score >= 0.7:
            level = SafetyLevel.CAUTION
        elif base_score >= 0.5:
            level = SafetyLevel.UNSAFE
        else:
            level = SafetyLevel.BLOCKED
        
        return SafetyScore(
            level=level,
            score=base_score,
            categories=scores,
            recommendations=recommendations
        )
