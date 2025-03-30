from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, List, Iterator
import uuid
import json
from pathlib import Path
import time
import sqlite3
import os
import sys

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
                        timestamp TEXT NOT NULL,
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

    def generate_call_id(self) -> str:
        return str(uuid.uuid4())
        
    def log_call(
        self,
        call_id: str,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any],
        start_time: datetime,
        error: Optional[str] = None,
        agent_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a tool execution"""
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms
        
        # Convert outputs to JSON-serializable format if needed
        if outputs and isinstance(outputs, dict):
            outputs = {k: str(v) if not isinstance(v, (str, int, float, bool, list, dict)) else v 
                      for k, v in outputs.items()}
        
        # Save to database
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT INTO tool_calls (
                        call_id, tool_name, timestamp, inputs, outputs, 
                        error, duration_ms, agent_metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call_id,
                    tool_name,
                    start_time.isoformat(),  # Store in ISO format
                    json.dumps(inputs),
                    json.dumps(outputs) if outputs else None,
                    error,
                    duration,
                    json.dumps(agent_metadata) if agent_metadata else None
                ))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving to database: {e}", file=sys.stderr)
        
        # Print to console for immediate feedback
        success = "✅" if not error else "❌"
        print(f"\n{tool_name}")
        print(f"Time: {start_time.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        print(f"\nDuration: {duration}ms {success}")
        if error:
            print(f"Error: {error}")
        print(f"\n{call_id}")
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        if outputs:
            print(f"Outputs: {json.dumps(outputs, indent=2)}")

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
        # Get the latest timestamp from the database
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT MAX(timestamp) as last_ts FROM tool_calls"
            row = conn.execute(query).fetchone()
            last_timestamp = row['last_ts'] if row['last_ts'] else '1970-01-01T00:00:00'
        
        while True:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    query = """
                        SELECT * FROM tool_calls 
                        WHERE timestamp > ?
                    """
                    params = [last_timestamp]
                    
                    if tool_name:
                        query += " AND tool_name = ?"
                        params.append(tool_name)
                    
                    query += " ORDER BY timestamp ASC"
                    
                    rows = conn.execute(query, params).fetchall()
                    for row in rows:
                        log = ToolCallLog(
                            call_id=row['call_id'],
                            tool_name=row['tool_name'],
                            timestamp=datetime.fromisoformat(row['timestamp']),  # Parse ISO format
                            inputs=json.loads(row['inputs']),
                            outputs=json.loads(row['outputs']) if row['outputs'] else None,
                            error=row['error'],
                            duration_ms=row['duration_ms'],
                            agent_metadata=json.loads(row['agent_metadata']) if row['agent_metadata'] else None
                        )
                        last_timestamp = row['timestamp']
                        yield log
                
                time.sleep(1)  # Wait before checking for new logs
                
            except Exception as e:
                print(f"Error watching logs: {e}", file=sys.stderr)
                time.sleep(1)  # Wait before retrying 