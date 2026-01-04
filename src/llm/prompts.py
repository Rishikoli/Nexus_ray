"""
Prompt templates for LLM tasks.

Provides structured prompts for different task types.
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class PromptTemplate(str, Enum):
    """Standard prompt templates"""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    REASONING = "reasoning"
    CODE_GENERATION = "code"
    JSON_MODE = "json"


# Template definitions
TEMPLATES = {
    PromptTemplate.ANALYSIS: """Analyze the following information and provide detailed insights:

{context}

Question: {query}

Provide a comprehensive analysis addressing:
1. Key findings
2. Important patterns or trends
3. Relevant implications
4. Actionable recommendations

Analysis:""",

    PromptTemplate.GENERATION: """Generate content based on the following requirements:

Context: {context}

Requirements:
{requirements}

Generate:""",

    PromptTemplate.EXTRACTION: """Extract specific information from the following text:

Text: {text}

Extract: {extract_keys}

Provide the extracted information in a clear, structured format.

Extracted Information:""",

    PromptTemplate.CLASSIFICATION: """Classify the following item into one of the specified categories:

Item: {item}

Categories: {categories}

Classification Rules:
{rules}

Provide your classification with reasoning.

Classification:""",

    PromptTemplate.REASONING: """Solve the following problem using step-by-step reasoning:

Problem: {problem}

Context: {context}

Think through this carefully and provide:
1. Your reasoning process
2. Key assumptions
3. Final answer or recommendation

Reasoning:""",

    PromptTemplate.CODE_GENERATION: """Generate code based on the following specification:

Language: {language}

Requirements:
{requirements}

Context: {context}

Generate clean, well-documented code.

Code:
```{language}""",

    PromptTemplate.JSON_MODE: """You are a precise data extraction system that outputs ONLY valid JSON.

Task: {task}

Input Data:
{input_data}

Output Schema:
{schema}

Rules:
1. Output ONLY valid JSON matching the schema
2. Do not include any explanatory text before or after the JSON
3. Ensure all required fields are present
4. Use appropriate data types

JSON Output:
```json"""
}


class PromptBuilder:
    """
    Flexible prompt builder with template support.
    
    Usage:
        prompt = PromptBuilder(PromptTemplate.ANALYSIS)
        prompt.set("context", "...")
        prompt.set("query", "...")
        result = prompt.build()
    """
    
    def __init__(self, template: Optional[PromptTemplate] = None, custom_template: Optional[str] = None):
        """
        Initialize prompt builder.
        
        Args:
            template: Standard template to use
            custom_template: Custom template string
        """
        if template:
            self.template = TEMPLATES[template]
        elif custom_template:
            self.template = custom_template
        else:
            self.template = "{content}"
        
        self.variables: Dict[str, Any] = {}
        self.system_prompt: Optional[str] = None
    
    def set(self, key: str, value: Any) -> "PromptBuilder":
        """
        Set template variable.
        
        Args:
            key: Variable name
            value: Variable value
            
        Returns:
            Self for chaining
        """
        self.variables[key] = str(value)
        return self
    
    def set_system(self, system_prompt: str) -> "PromptBuilder":
        """
        Set system prompt (for chat models).
        
        Args:
            system_prompt: System message
            
        Returns:
            Self for chaining
        """
        self.system_prompt = system_prompt
        return self
    
    def build(self) -> str:
        """
        Build final prompt.
        
        Returns:
            Formatted prompt string
        """
        try:
            return self.template.format(**self.variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def build_messages(self) -> List[Dict[str, str]]:
        """
        Build chat messages format.
        
        Returns:
            List of message dicts
        """
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        messages.append({"role": "user", "content": self.build()})
        
        return messages


def create_task_prompt(
    task_type: str,
    task_description: str,
    inputs: Dict[str, Any],
    context: Optional[str] = None
) -> str:
    """
    Create prompt for task execution.
    
    Args:
        task_type: Type of task (llm, tool, etc.)
        task_description: Task description
        inputs: Task inputs
        context: Additional context
        
    Returns:
        Formatted prompt
    """
    prompt_parts = []
    
    # Add context if provided
    if context:
        prompt_parts.append(f"Context:\n{context}\n")
    
    # Add task description
    prompt_parts.append(f"Task: {task_description}\n")
    
    # Add inputs
    if inputs:
        prompt_parts.append("Inputs:")
        for key, value in inputs.items():
            prompt_parts.append(f"  - {key}: {value}")
        prompt_parts.append("")
    
    # Add instructions
    prompt_parts.append("Please complete this task and provide your response.")
    
    return "\n".join(prompt_parts)


def create_json_prompt(
    task: str,
    input_data: Any,
    schema: Dict[str, Any],
    examples: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create prompt for JSON-mode output.
    
    Args:
        task: Task description
        input_data: Input data
        schema: Expected JSON schema
        examples: Optional example outputs
        
    Returns:
        JSON-mode prompt
    """
    builder = PromptBuilder(PromptTemplate.JSON_MODE)
    builder.set("task", task)
    builder.set("input_data", str(input_data))
    builder.set("schema", str(schema))
    
    return builder.build()


def create_few_shot_prompt(
    task: str,
    examples: List[Dict[str, str]],
    query: str
) -> str:
    """
    Create few-shot learning prompt.
    
    Args:
        task: Task description
        examples: List of {"input": "...", "output": "..."} examples
        query: Current query
        
    Returns:
        Few-shot prompt
    """
    prompt_parts = [f"Task: {task}\n"]
    
    # Add examples
    prompt_parts.append("Examples:")
    for i, example in enumerate(examples, 1):
        prompt_parts.append(f"\nExample {i}:")
        prompt_parts.append(f"Input: {example['input']}")
        prompt_parts.append(f"Output: {example['output']}")
    
    # Add query
    prompt_parts.append(f"\nNow solve this:")
    prompt_parts.append(f"Input: {query}")
    prompt_parts.append(f"Output:")
    
    return "\n".join(prompt_parts)
