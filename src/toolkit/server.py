from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import importlib.util
import sys
from pathlib import Path
import logging
from inspect import getmembers
import time
from .logging import ToolLogger

from .core import ToolRegistry

app = FastAPI(title="B2A Toolkit Server")
registry = ToolRegistry()
logger = ToolLogger()  # Initialize the logger

class ToolRequest(BaseModel):
    inputs: Dict[str, Any]

@app.get("/manifest.json")
async def get_manifest():
    """Return the complete tool manifest"""
    tools = registry.list_tools()
    return {
        "total_tools": len(tools),
        "tools": tools
    }

@app.post("/run/{tool_name}")
async def run_tool(tool_name: str, request: Dict[str, Any]):
    """Execute a specific tool with given inputs"""
    if tool_name not in registry.tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
    tool = registry.tools[tool_name]
    inputs = request.get("inputs", {})
    
    start_time = time.time()
    try:
        # Execute the tool
        result = await tool.execute(**inputs)
        
        # Log successful execution
        duration_ms = (time.time() - start_time) * 1000
        logger.log_call(
            tool_name=tool_name,
            inputs=inputs,
            outputs=result,
            duration_ms=duration_ms,
            agent_metadata=request.get("agent_metadata")
        )
        
        return {"outputs": result}
        
    except Exception as e:
        # Log failed execution
        duration_ms = (time.time() - start_time) * 1000
        logger.log_call(
            tool_name=tool_name,
            inputs=inputs,
            error=str(e),
            duration_ms=duration_ms,
            agent_metadata=request.get("agent_metadata")
        )
        raise HTTPException(status_code=500, detail=str(e))

def _load_module(module_path: Path) -> object:
    """Load a Python module from a file path using importlib"""
    try:
        spec = importlib.util.spec_from_file_location(module_path.stem, str(module_path))
        if spec is None:
            raise ImportError(f"Could not load module spec from {module_path}")
            
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not load module loader from {module_path}")
            
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        raise ImportError(f"Failed to load module {module_path}: {e}")

def load_tools_from_path(module_path: str):
    """Load tools from a Python module"""
    try:
        module = _load_module(Path(module_path))
        for name, obj in getmembers(module):
            if hasattr(obj, 'tool'):
                registry.register(obj.tool)
    except Exception as e:
        raise ImportError(f"Failed to load tools from {module_path}: {e}")

def register_tool(tool):
    """Register a tool with the server"""
    registry.register(tool) 