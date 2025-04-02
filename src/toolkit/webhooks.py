from dataclasses import dataclass
from typing import Dict, List, Optional
import httpx
import asyncio
from datetime import datetime
import json
import sqlite3
import os
from pathlib import Path
import sys

@dataclass
class WebhookConfig:
    url: str
    tool_name: Optional[str] = None  # None means global webhook
    secret: Optional[str] = None
    retries: int = 3

class WebhookManager:
    def __init__(self):
        self._webhooks: List[WebhookConfig] = []
        self._client = httpx.AsyncClient(timeout=10.0)
        
        # Use ~/.toolkit directory like logging
        storage_path = Path(os.path.expanduser("~/.toolkit"))
        storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = storage_path / "webhooks.db"
        
        self._init_db()
        self._load_webhooks()
    
    def _init_db(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS webhooks (
                        url TEXT NOT NULL,
                        tool_name TEXT,
                        secret TEXT,
                        retries INTEGER DEFAULT 3,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (url, tool_name)
                    )
                """)
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Failed to initialize database at {self.db_path}: {e}")

    def _load_webhooks(self) -> None:
        """Load webhooks from database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM webhooks").fetchall()
                self._webhooks = [
                    WebhookConfig(
                        url=row['url'],
                        tool_name=row['tool_name'],
                        secret=row['secret'],
                        retries=row['retries']
                    ) for row in rows
                ]
        except sqlite3.Error as e:
            print(f"Error loading webhooks: {e}", file=sys.stderr)
            self._webhooks = []

    def add_webhook(self, url: str, tool_name: Optional[str] = None, secret: Optional[str] = None) -> None:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO webhooks (url, tool_name, secret)
                    VALUES (?, ?, ?)
                """, (url, tool_name, secret))
            # Reload webhooks from db
            self._load_webhooks()
        except sqlite3.Error as e:
            print(f"Error adding webhook: {e}", file=sys.stderr)
            raise

    def remove_webhook(self, url: str, tool_name: Optional[str] = None) -> None:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    DELETE FROM webhooks 
                    WHERE url = ? AND (tool_name = ? OR (tool_name IS NULL AND ? IS NULL))
                """, (url, tool_name, tool_name))
            # Reload webhooks from db
            self._load_webhooks()
        except sqlite3.Error as e:
            print(f"Error removing webhook: {e}", file=sys.stderr)
            raise

    def list_webhooks(self) -> List[Dict]:
        return [
            {
                "url": w.url,
                "tool_name": w.tool_name,
                "active": True
            }
            for w in self._webhooks
        ]

    def _sign_payload(self, payload: Dict, secret: Optional[str]) -> Optional[str]:
        # Add missing signature method
        if not secret:
            return None
        # Implement your signature logic here
        # For example, using HMAC:
        import hmac
        import hashlib
        message = json.dumps(payload).encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    async def close(self):
        # Add cleanup method
        await self._client.aclose()

    async def trigger(self, event_type: str, tool_name: str, data: Dict) -> None:
        payload = {
            "event": event_type,
            "tool": tool_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Find matching webhooks (global + tool-specific)
        matching_hooks = [
            w for w in self._webhooks 
            if w.tool_name is None or w.tool_name == tool_name
        ]
        
        # Fire all webhooks concurrently
        await asyncio.gather(*[
            self._send_webhook(hook, payload) 
            for hook in matching_hooks
        ])
    
    async def _send_webhook(self, config: WebhookConfig, payload: Dict) -> None:
        for attempt in range(config.retries):
            try:
                # Build headers
                headers = {"Content-Type": "application/json"}
                
                # Only add signature header if we have a signature
                signature = self._sign_payload(payload, config.secret)
                if signature:
                    headers["X-B2A-Signature"] = signature
                
                response = await self._client.post(
                    config.url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return
            except Exception as e:
                if attempt == config.retries - 1:
                    # Log final failure
                    print(f"Failed to send webhook to {config.url}: {e}") 