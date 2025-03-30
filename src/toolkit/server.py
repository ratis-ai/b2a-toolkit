from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import importlib.util
import sys
from pathlib import Path
import logging

from .core import ToolRegistry

app = FastAPI(title="B2A Toolkit Server")
registry = ToolRegistry()

# Add logging
logger = logging.getLogger(__name__)

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
async def run_tool(tool_name: str, request: ToolRequest):
    """Execute a specific tool with given inputs"""
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        result = tool(**request.inputs)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def load_tools_from_path(path: str):
    """Load all tools from a Python module"""
    path = Path(path)
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    
    logger.info(f"Loading tools from {path}")
    
    # Import the module dynamically
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        raise ValueError(f"Could not load module: {path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    
    # Register tools found in the module
    tools_found = len(registry.tools)
    logger.info(f"Found {tools_found} tools in module")
    
    return tools_found 