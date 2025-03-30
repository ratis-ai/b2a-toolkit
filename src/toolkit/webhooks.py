from dataclasses import dataclass
from typing import Dict, List, Optional
import httpx
import asyncio
from datetime import datetime
import json

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
    
    def add_webhook(self, config: WebhookConfig) -> None:
        self._webhooks.append(config)
    
    def remove_webhook(self, url: str, tool_name: Optional[str] = None) -> None:
        self._webhooks = [w for w in self._webhooks 
                         if not (w.url == url and w.tool_name == tool_name)]

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
                response = await self._client.post(
                    config.url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-B2A-Signature": self._sign_payload(payload, config.secret)
                    }
                )
                response.raise_for_status()
                return
            except Exception as e:
                if attempt == config.retries - 1:
                    # Log final failure
                    print(f"Failed to send webhook to {config.url}: {e}") 