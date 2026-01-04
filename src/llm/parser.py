"""
Response parser for LLM outputs.

Handles JSON extraction and structured output parsing.
"""

import json
import re
from typing import Dict, Any, Optional, List
from loguru import logger

from src.core.exceptions import InferenceError


class ResponseParser:
    """
    Parser for LLM responses with JSON extraction.
    
    Features:
    - Extract JSON from text responses
    - Validate against schemas
    - Handle malformed JSON
    - Extract code blocks
    """
    
    @staticmethod
    def extract_json(text: str, strict: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from LLM response.
        
        Args:
            text: Response text
            strict: If True, raise error on parse failure
            
        Returns:
            Parsed JSON dict or None
        """
        # Try direct JSON parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in code blocks
        json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_blocks:
            try:
                return json.loads(json_blocks[0])
            except json.JSONDecodeError as e:
                if strict:
                    raise InferenceError(f"Invalid JSON in code block: {e}")
                logger.warning(f"Failed to parse JSON from code block: {e}")
        
        # Try to find JSON-like structures
        # Look for {...} patterns
        json_patterns = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        for pattern in json_patterns:
            try:
                return json.loads(pattern)
            except json.JSONDecodeError:
                continue
        
        if strict:
            raise InferenceError(f"No valid JSON found in response: {text[:200]}")
        
        return None
    
    @staticmethod
    def extract_code(text: str, language: Optional[str] = None) -> Optional[str]:
        """
        Extract code from markdown code blocks.
        
        Args:
            text: Response text
            language: Specific language to extract (None for any)
            
        Returns:
            Extracted code or None
        """
        if language:
            pattern = rf'```{language}\s*(.*?)\s*```'
        else:
            pattern = r'```(?:\w+)?\s*(.*?)\s*```'
        
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        return None
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Simple schema validation.
        
        Args:
            data: Data to validate
            schema: Schema dict with {"field": "type"} format
            
        Returns:
            True if valid
        """
        for field, field_type in schema.items():
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
            
            # Type checking
            if field_type == "string" and not isinstance(data[field], str):
                logger.warning(f"Field {field} should be string, got {type(data[field])}")
                return False
            elif field_type == "number" and not isinstance(data[field], (int, float)):
                logger.warning(f"Field {field} should be number, got {type(data[field])}")
                return False
            elif field_type == "boolean" and not isinstance(data[field], bool):
                logger.warning(f"Field {field} should be boolean, got {type(data[field])}")
                return False
            elif field_type == "array" and not isinstance(data[field], list):
                logger.warning(f"Field {field} should be array, got {type(data[field])}")
                return False
            elif field_type == "object" and not isinstance(data[field], dict):
                logger.warning(f"Field {field} should be object, got {type(data[field])}")
                return False
        
        return True
    
    @staticmethod
    def extract_list(text: str) -> List[str]:
        """
        Extract list items from text.
        
        Args:
            text: Text containing list
            
        Returns:
            List of items
        """
        # Try numbered list (1. item, 2. item)
        numbered = re.findall(r'^\d+\.\s*(.+)$', text, re.MULTILINE)
        if numbered:
            return [item.strip() for item in numbered]
        
        # Try bulleted list (- item, * item)
        bulleted = re.findall(r'^[\-\*]\s*(.+)$', text, re.MULTILINE)
        if bulleted:
            return [item.strip() for item in bulleted]
        
        # Fallback: split by newlines
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    @staticmethod
    def clean_response(text: str) -> str:
        """
        Clean LLM response (remove artifacts, extra whitespace).
        
        Args:
            text: Raw response
            
        Returns:
            Cleaned text
        """
        # Remove common artifacts
        text = re.sub(r'<\|im_end\|>', '', text)
        text = re.sub(r'</s>', '', text)
        text = re.sub(r'<\|endoftext\|>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = text.strip()
        
        return text


def parse_llm_output(
    text: str,
    output_type: str = "text",
    schema: Optional[Dict[str, Any]] = None,
    strict: bool = False
) -> Any:
    """
    Parse LLM output based on expected type.
    
    Args:
        text: Raw LLM output
        output_type: Expected type (text, json, code, list)
        schema: Optional schema for validation
        strict: Strict parsing mode
        
    Returns:
        Parsed output
    """
    parser = ResponseParser()
    
    # Clean response first
    text = parser.clean_response(text)
    
    if output_type == "json":
        result = parser.extract_json(text, strict=strict)
        if result and schema:
            if not parser.validate_schema(result, schema):
                if strict:
                    raise InferenceError("Response does not match schema")
                logger.warning("Response schema validation failed")
        return result
    
    elif output_type == "code":
        return parser.extract_code(text)
    
    elif output_type == "list":
        return parser.extract_list(text)
    
    else:  # text
        return text
