"""
SDK for defining and registering tools.
"""

from typing import Callable, Optional, Dict, Any, List
import functools
from loguru import logger

# Global tool registry
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to register a function as a tool.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        
    Example:
        @tool(name="calculator")
        def add(a: int, b: int) -> int:
            "Adds two numbers"
            return a + b
    """
    def decorator(func: Callable):
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or "No description provided"
        
        # Register tool
        _TOOL_REGISTRY[tool_name] = {
            "name": tool_name,
            "description": tool_desc.strip(),
            "function": func,
            "parameters": func.__annotations__
        }
        
        logger.debug(f"Registered tool: {tool_name}")
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_tool(name: str) -> Optional[Callable]:
    """Get a registered tool function"""
    if name not in _TOOL_REGISTRY:
        return None
    return _TOOL_REGISTRY[name]["function"]


def list_tools() -> List[Dict[str, Any]]:
    """List all registered tools"""
    return [
        {
            "name": t["name"],
            "description": t["description"]
        }
        for t in _TOOL_REGISTRY.values()
    ]
