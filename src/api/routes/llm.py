"""
LLM API routes.
"""

from fastapi import APIRouter, HTTPException
import time

from src.api.models import LLMGenerateRequest, LLMGenerateResponse
from src.llm import get_llm

router = APIRouter()


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate_text(request: LLMGenerateRequest):
    """Generate text using LLM"""
    try:
        llm = get_llm()
        
        start_time = time.time()
        response = llm.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        latency = time.time() - start_time
        
        # Rough token estimation
        tokens_used = len(response.split())
        
        return LLMGenerateResponse(
            text=response,
            tokens_used=tokens_used,
            latency=latency,
            model="mistral-7b-ov"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {
                "id": "mistral-7b-ov",
                "name": "Mistral 7B (OpenVINO)",
                "status": "available",
                "backend": "openvino"
            }
        ]
    }


@router.get("/metrics")
async def get_llm_metrics():
    """Get LLM metrics"""
    # In production, get from observability system
    return {
        "total_calls": 0,
        "total_tokens": 0,
        "avg_latency": 0,
        "cost_estimate": 0
    }
