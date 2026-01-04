"""
Custom exceptions for Nexus Ray framework.

Provides detailed error types for better error handling.
"""


class NexusRayError(Exception):
    """Base exception for all Nexus Ray errors"""
    pass


# ===== Core Framework Errors =====

class WorkflowError(NexusRayError):
    """Base exception for workflow-related errors"""
    pass


class DAGError(WorkflowError):
    """Base exception for DAG-related errors"""
    pass


class CyclicDependencyError(DAGError):
    """Raised when a cycle is detected in the DAG"""
    pass


class TaskNotFoundError(DAGError):
    """Raised when a task is not found in the DAG"""
    pass


class InvalidWorkflowError(WorkflowError):
    """Raised when workflow definition is invalid"""
    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails"""
    pass


class WorkflowTimeoutError(WorkflowError):
    """Raised when workflow times out"""
    pass


class TaskExecutionError(WorkflowError):
    """Raised when task execution fails"""
    pass


class TaskTimeoutError(TaskExecutionError):
    """Raised when task times out"""
    pass


# ===== Executor Errors =====

class ExecutorError(NexusRayError):
    """Base exception for executor errors"""
    pass


class LLMExecutorError(ExecutorError):
    """Raised when LLM execution fails"""
    pass


class ToolExecutorError(ExecutorError):
    """Raised when tool execution fails"""
    pass


class AgentExecutorError(ExecutorError):
    """Raised when agent execution fails"""
    pass


# ===== Messaging Errors =====

class MessagingError(NexusRayError):
    """Base exception for messaging errors"""
    pass


class KafkaConnectionError(MessagingError):
    """Raised when Kafka connection fails"""
    pass


class MessageSerializationError(MessagingError):
    """Raised when message serialization fails"""
    pass


class TopicNotFoundError(MessagingError):
    """Raised when Kafka topic is not found"""
    pass


# ===== Memory Errors =====

class MemoryError(NexusRayError):
    """Base exception for memory-related errors"""
    pass


class VectorMemoryError(MemoryError):
    """Raised when vector memory operation fails"""
    pass


class EmbeddingError(MemoryError):
    """Raised when embedding generation fails"""
    pass


class MemoryRetrievalError(MemoryError):
    """Raised when memory retrieval fails"""
    pass


# ===== LLM Errors =====

class LLMError(NexusRayError):
    """Base exception for LLM-related errors"""
    pass


class ModelLoadError(LLMError):
    """Raised when model loading fails"""
    pass


class InferenceError(LLMError):
    """Raised when LLM inference fails"""
    pass


class TokenLimitError(LLMError):
    """Raised when token limit is exceeded"""
    pass


# ===== Guardrail Errors =====

class GuardrailError(NexusRayError):
    """Base exception for guardrail violations"""
    pass


class InputValidationError(GuardrailError):
    """Raised when input validation fails"""
    pass


class OutputValidationError(GuardrailError):
    """Raised when output validation fails"""
    pass


class PolicyViolationError(GuardrailError):
    """Raised when a policy is violated"""
    pass


class ContentFilterError(GuardrailError):
    """Raised when content filtering detects violations"""
    pass


# ===== HITL Errors =====

class HITLError(NexusRayError):
    """Base exception for HITL-related errors"""
    pass


class ApprovalTimeoutError(HITLError):
    """Raised when approval times out"""
    pass


class ApprovalRejectedError(HITLError):
    """Raised when approval is rejected"""
    pass


# ===== Configuration Errors =====

class ConfigurationError(NexusRayError):
    """Raised when configuration is invalid"""
    pass


# ===== API Errors =====

class APIError(NexusRayError):
    """Base exception for API errors"""
    pass


class ResourceNotFoundError(APIError):
    """Raised when a resource is not found"""
    pass


class UnauthorizedError(APIError):
    """Raised when authentication fails"""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded"""
    pass
