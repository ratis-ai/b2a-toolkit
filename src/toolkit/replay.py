from typing import Dict, Any, Optional
from datetime import datetime
import json
import sqlite3
import os
from pathlib import Path

class ReplayManager:
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            # Use ~/.toolkit/logs as default storage location
            storage_path = os.path.expanduser("~/.toolkit/logs")
        
        # Convert to absolute path and ensure directory exists
        self.storage_path = Path(storage_path).absolute()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Use the same database file as ToolLogger
        self.db_path = self.storage_path / "tools.db"
    
    def get_call(self, call_id: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM tool_calls WHERE call_id = ?
                """, (call_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise FileNotFoundError(f"Call ID {call_id} not found in logs")
                    
                return {
                    "id": row['call_id'],
                    "tool": row['tool_name'],
                    "timestamp": row['timestamp'],
                    "inputs": json.loads(row['inputs']),
                    "outputs": json.loads(row['outputs']) if row['outputs'] else None,
                    "error": row['error']
                }
        except sqlite3.OperationalError as e:
            raise FileNotFoundError(f"Error accessing logs database: {e}")
    
    def replay_call(self, call_id: str, tool_registry) -> Dict[str, Any]:
        # Load original call
        call_data = self.get_call(call_id)
        
        # Get tool
        tool = tool_registry.get_tool(call_data["tool"])
        if not tool:
            raise ValueError(f"Tool '{call_data['tool']}' not found in the provided module")
            
        # Execute tool with original inputs
        try:
            # Call the function directly instead of using execute
            result = tool.func(**call_data["inputs"])
            return {
                "original_call": call_data,
                "replay_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "original_call": call_data,
                "replay_error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 