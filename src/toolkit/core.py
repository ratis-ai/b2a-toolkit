"""
Core functionality for ToolPilot
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union
from .types import ToolAuth, ToolInput, ToolOutput
from dataclasses import dataclass, asdict
import asyncio
from datetime import datetime
from .logging import ToolLogger

@dataclass
class ToolAuth:
    required: bool
    scopes: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required": self.required,
            "scopes": self.scopes or []
        }

@dataclass
class ToolMetadata:
    name: str
    description: str
    inputs: Dict[str, str]
    output_description: Optional[str] = None
    auth: Optional[ToolAuth] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format"""
        result = {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "output_description": self.output_description,
        }
        
        if self.auth is not None:
            result["auth"] = self.auth.to_dict()
            
        return result

class Tool:
    """Represents a tool that can be used by AI agents"""
    def __init__(self, metadata: ToolMetadata, func: callable):
        self.metadata = metadata
        self._func = func
        self._logger = ToolLogger()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format"""
        return self.metadata.to_dict()
        
    async def execute(self, **inputs: Dict[str, Any]) -> Any:
        """Execute the tool with the given inputs"""
        if not self._func:
            raise RuntimeError("No function implementation provided for tool")
        
        call_id = self._logger.generate_call_id()
        start_time = datetime.utcnow()
        
        try:
            # If the function is async, await it, otherwise run it directly
            if asyncio.iscoroutinefunction(self._func):
                result = await self._func(**inputs)
            else:
                result = self._func(**inputs)
                
            # Log successful execution
            self._logger.log_call(
                call_id=call_id,
                tool_name=self.metadata.name,
                inputs=inputs,
                outputs=result,
                start_time=start_time,
                error=None
            )
            
            return result
            
        except Exception as e:
            # Log failed execution
            self._logger.log_call(
                call_id=call_id,
                tool_name=self.metadata.name,
                inputs=inputs,
                outputs=None,
                start_time=start_time,
                error=str(e)
            )
            raise e

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
        # Convert auth dict to ToolAuth object if present
        auth_config = tool_config.get('auth')
        auth = None
        if auth_config:
            auth = ToolAuth(
                required=auth_config.get('required', False),
                scopes=auth_config.get('scopes', [])
            )
        
        metadata = ToolMetadata(
            name=tool_config['name'],
            description=tool_config['description'],
            inputs=tool_config.get('inputs', {}),
            output_description=tool_config.get('output_description'),
            auth=auth
        )
        
        tool = Tool(metadata=metadata, func=func)
        registry.register(tool)  # Register the tool
        func.tool = tool  # Attach tool to the function
        return func
        
    return decorator 