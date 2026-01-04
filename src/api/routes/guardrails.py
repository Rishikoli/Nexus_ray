"""
Guardrails API routes.
"""

from fastapi import APIRouter

from src.api.models import (
    ContentFilterRequest,
    ContentFilterResponse,
    SafetyScoreResponse
)
from src.guardrails import ContentFilter, SafetyScorer

router = APIRouter()


@router.post("/filter", response_model=ContentFilterResponse)
async def filter_content(request: ContentFilterRequest):
    """Filter content for safety"""
    filter = ContentFilter()
    
    result = filter.filter(request.text, strict_mode=request.strict_mode)
    
    return ContentFilterResponse(
        passed=result.passed,
        blocked_categories=[c.value for c in result.blocked_categories],
        sanitized_text=result.sanitized_text,
        confidence=result.confidence
    )


@router.post("/score", response_model=SafetyScoreResponse)
async def safety_score(request: ContentFilterRequest):
    """Get safety score for content"""
    filter = ContentFilter()
    scorer = SafetyScorer()
    
    filter_result = filter.filter(request.text, strict_mode=request.strict_mode)
    safety = scorer.score(request.text, filter_result, [])
    
    return SafetyScoreResponse(
        level=safety.level.value,
        score=safety.score,
        categories=safety.categories,
        recommendations=safety.recommendations
    )
