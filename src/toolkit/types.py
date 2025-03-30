"""
Core type definitions for ToolPilot
"""
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field

class ToolAuth(BaseModel):
    """Authentication configuration for a tool"""
    type: str = Field(..., description="Authentication type (e.g., 'oauth', 'api_key', 'none')")
    required: bool = Field(default=True, description="Whether authentication is required")
    scopes: Optional[List[str]] = Field(default=None, description="Required OAuth scopes if applicable")

class ToolInput(BaseModel):
    """Input parameter definition for a tool"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (e.g., 'string', 'number', 'boolean')")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether the parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if any")

class ToolOutput(BaseModel):
    """Output definition for a tool"""
    type: str = Field(..., description="Output type (e.g., 'object', 'array', 'string')")
    description: str = Field(..., description="Output description")
    json_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON Schema for the output")

class ToolMetadata(BaseModel):
    """Metadata about a tool"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    version: str = Field(..., description="Tool version")
    inputs: List[ToolInput] = Field(default_factory=list, description="Input parameters")
    output: ToolOutput = Field(..., description="Output definition")
    auth: ToolAuth = Field(default_factory=lambda: ToolAuth(type="none", required=False), description="Authentication config")
    tags: List[str] = Field(default_factory=list, description="Tool tags/categories") 