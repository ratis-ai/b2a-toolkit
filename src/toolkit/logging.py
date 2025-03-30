from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, List, Iterator
import uuid
import json
from pathlib import Path
import time
import sqlite3
import os

@dataclass
class ToolCallLog:
    call_id: str
    tool_name: str
    timestamp: datetime
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: float
    agent_metadata: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'call_id': self.call_id,
            'tool_name': self.tool_name,
            'timestamp': self.timestamp.isoformat(),
            'inputs': self.inputs,
            'outputs': self.outputs,
            'error': self.error,
            'duration_ms': self.duration_ms,
            'agent_metadata': self.agent_metadata
        }

class ToolLogger:
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            # Use ~/.toolkit/logs as default storage location
            storage_path = os.path.expanduser("~/.toolkit/logs")
        
        # Convert to absolute path and ensure directory exists
        self.storage_path = Path(storage_path).absolute()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create database file path
        self.db_path = self.storage_path / "tools.db"
        
        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        try:
            db_path_str = str(self.db_path)
            with sqlite3.connect(db_path_str) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tool_calls (
                        call_id TEXT PRIMARY KEY,
                        tool_name TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        inputs TEXT NOT NULL,
                        outputs TEXT,
                        error TEXT,
                        duration_ms REAL NOT NULL,
                        agent_metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Add an index on timestamp for better query performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON tool_calls(timestamp DESC)
                """)
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Failed to initialize database at {self.db_path}: {e}")

    def log_call(self, 
                 tool_name: str,
                 inputs: Dict[str, Any],
                 outputs: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None,
                 duration_ms: float = 0,
                 agent_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a tool call"""
        call_id = str(uuid.uuid4())
        with sqlite3.connect(str(self.db_path)) as conn:  # Convert Path to string
            conn.execute("""
                INSERT INTO tool_calls 
                (call_id, tool_name, timestamp, inputs, outputs, error, duration_ms, agent_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                tool_name,
                datetime.utcnow().isoformat(),
                json.dumps(inputs),
                json.dumps(outputs) if outputs else None,
                error,
                duration_ms,
                json.dumps(agent_metadata) if agent_metadata else None
            ))
        return call_id

    def get_logs(self, tool_name: Optional[str] = None, limit: int = 10) -> List[ToolCallLog]:
        """Retrieve logs with optional filtering"""
        with sqlite3.connect(str(self.db_path)) as conn:  # Convert Path to string
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM tool_calls"
            params = []
            
            if tool_name:
                query += " WHERE tool_name = ?"
                params.append(tool_name)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            return [ToolCallLog(
                call_id=row['call_id'],
                tool_name=row['tool_name'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                inputs=json.loads(row['inputs']),
                outputs=json.loads(row['outputs']) if row['outputs'] else None,
                error=row['error'],
                duration_ms=row['duration_ms'],
                agent_metadata=json.loads(row['agent_metadata']) if row['agent_metadata'] else None
            ) for row in rows]

    def watch_logs(self, tool_name: Optional[str] = None) -> Iterator[ToolCallLog]:
        """Watch for new logs in real-time"""
        last_timestamp = datetime.utcnow()
        
        while True:
            with sqlite3.connect(str(self.db_path)) as conn:  # Convert Path to string
                conn.row_factory = sqlite3.Row
                query = "SELECT * FROM tool_calls WHERE timestamp > ?"
                params = [last_timestamp.isoformat()]
                
                if tool_name:
                    query += " AND tool_name = ?"
                    params.append(tool_name)
                
                query += " ORDER BY timestamp ASC"
                
                for row in conn.execute(query, params):
                    log = ToolCallLog(
                        call_id=row['call_id'],
                        tool_name=row['tool_name'],
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        inputs=json.loads(row['inputs']),
                        outputs=json.loads(row['outputs']) if row['outputs'] else None,
                        error=row['error'],
                        duration_ms=row['duration_ms'],
                        agent_metadata=json.loads(row['agent_metadata']) if row['agent_metadata'] else None
                    )
                    last_timestamp = log.timestamp
                    yield log
            
            time.sleep(1)  # Wait before checking for new logs 