"""
SDK for defining execution policies.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    """
    Configuration for retry behavior.
    """
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    backoff_factor: float = Field(default=1.5, description="Exponential backoff multiplier")
    retry_on_exceptions: List[str] = Field(default_factory=list, description="List of exception names to retry on")


class TimeoutPolicy(BaseModel):
    """
    Configuration for timeout behavior.
    """
    timeout_seconds: int = Field(..., description="Maximum execution time in seconds")
    strict: bool = Field(default=True, description="Whether to kill the task immediately on timeout")


class SecurityPolicy(BaseModel):
    """
    Configuration for security guardrails.
    """
    block_unsafe_content: bool = Field(default=True, description="Block unsafe LLM outputs")
    pii_redaction: bool = Field(default=False, description="Redact PII from logs/outputs")
    allowed_tools: Optional[List[str]] = Field(default=None, description="Allowlist of tools")


class ExecutionPolicy(BaseModel):
    """
    Combined execution policy.
    """
    retry: Optional[RetryPolicy] = None
    timeout: Optional[TimeoutPolicy] = None
    security: Optional[SecurityPolicy] = None
    
    @classmethod
    def default(cls) -> 'ExecutionPolicy':
        """Get default policy"""
        return cls(
            retry=RetryPolicy(),
            timeout=TimeoutPolicy(timeout_seconds=60),
            security=SecurityPolicy()
        )
