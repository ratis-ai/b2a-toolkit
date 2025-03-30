"""
Core functionality for ToolPilot
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union
from .types import ToolAuth, ToolInput, ToolOutput, ToolMetadata

class Tool:
    """Represents a tool that can be used by AI agents"""
    def __init__(
        self,
        func: Callable,
        name: str,
        description: str,
        inputs: Dict[str, str],
        output_type: str,
        output_description: str,
        auth: Optional[ToolAuth] = None,
        version: str = "0.1.0",
        tags: Optional[List[str]] = None
    ):
        self.func = func
        self.metadata = ToolMetadata(
            name=name,
            description=description,
            version=version,
            inputs=[
                ToolInput(
                    name=name,
                    type=type_,
                    description=f"Input parameter {name}",
                    required=True
                )
                for name, type_ in inputs.items()
            ],
            output=ToolOutput(
                type=output_type,
                description=output_description
            ),
            auth=auth or ToolAuth(type="none", required=False),
            tags=tags or []
        )
        
    def __call__(self, *args, **kwargs):
        """Execute the tool with the given arguments"""
        return self.func(*args, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary format"""
        return self.metadata.model_dump()

class ToolRegistry:
    """Registry for managing tools"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tools = {}
        return cls._instance
    
    def register(self, tool: 'Tool') -> None:
        """Register a new tool"""
        self.tools[tool.metadata.name] = tool
        
    def get_tool(self, name: str) -> Optional['Tool']:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [tool.to_dict() for tool in self.tools.values()]

# Make registry a singleton
registry = ToolRegistry()

def define_tool(
    name: str,
    description: str,
    inputs: Dict[str, str],
    output_type: str,
    output_description: str,
    auth: Optional[ToolAuth] = None,
    version: str = "0.1.0",
    tags: Optional[List[str]] = None
) -> Callable:
    """
    Decorator to define a new tool
    
    Args:
        name: Name of the tool
        description: Description of what the tool does
        inputs: Dictionary mapping input parameter names to their types
        output_type: Type of the tool's output
        output_description: Description of the tool's output
        auth: Optional authentication configuration
        version: Version of the tool
        tags: Optional list of tags/categories
    
    Returns:
        A decorator that can be used to define a tool
    """
    def decorator(func: Callable) -> Callable:
        tool = Tool(
            func=func,
            name=name,
            description=description,
            inputs=inputs,
            output_type=output_type,
            output_description=output_description,
            auth=auth,
            version=version,
            tags=tags
        )
        registry.register(tool)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return tool(*args, **kwargs)
            
        wrapper.tool = tool
        return wrapper
    return decorator 