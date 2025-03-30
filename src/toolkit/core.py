"""
Core functionality for ToolPilot
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union
from .types import ToolAuth, ToolInput, ToolOutput
from dataclasses import dataclass

@dataclass
class ToolMetadata:
    name: str
    description: str
    inputs: list
    output_description: Optional[str] = None
    auth: Optional[Any] = None

class Tool:
    """Represents a tool that can be used by AI agents"""
    def __init__(self, metadata: ToolMetadata, func: callable):
        self.metadata = metadata
        self._func = func
        
    async def execute(self, **inputs: Dict[str, Any]) -> Any:
        """Execute the tool with the given inputs"""
        # TODO: Add input validation here
        if not self._func:
            raise RuntimeError("No function implementation provided for tool")
            
        # If the function is async, await it, otherwise run it directly
        if hasattr(self._func, '__await__'):
            result = await self._func(**inputs)
        else:
            result = self._func(**inputs)
            
        return result

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

def define_tool(**tool_config):
    """Decorator to define a tool"""
    def decorator(func):
        metadata = ToolMetadata(
            name=tool_config['name'],
            description=tool_config['description'],
            inputs=tool_config.get('inputs', []),
            output_description=tool_config.get('output_description'),
            auth=tool_config.get('auth')
        )
        
        tool = Tool(metadata=metadata, func=func)
        func.tool = tool
        return func
        
    return decorator 