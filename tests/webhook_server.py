from fastapi import FastAPI, Request, Header
import uvicorn
from datetime import datetime
import hmac
import hashlib
import json

app = FastAPI(title="Test Webhook Server")

# Store received webhooks in memory for inspection
webhook_history = []

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature"""
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.post("/webhook")
async def webhook(request: Request, x_b2a_signature: str = Header(None)):
    """Receive and log webhook calls"""
    # Get raw body for signature verification
    body = await request.body()
    payload = await request.json()
    
    # Record webhook receipt
    webhook_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
        "headers": dict(request.headers),
        "signature_valid": None
    }

    # If there's a signature, verify it with test secret
    if x_b2a_signature:
        webhook_entry["signature_valid"] = verify_signature(
            body,
            x_b2a_signature,
            "test-secret"  # Use this secret when testing
        )

    webhook_history.append(webhook_entry)
    print(f"\n📥 Received webhook: {json.dumps(payload, indent=2)}")
    return {"status": "success"}

@app.get("/history")
async def get_history():
    """Get webhook receipt history"""
    return webhook_history

@app.delete("/history")
async def clear_history():
    """Clear webhook history"""
    webhook_history.clear()
    return {"status": "cleared"}

def start_server(host="127.0.0.1", port=8765):
    """Start the webhook test server"""
    print(f"\n🚀 Starting webhook test server at http://{host}:{port}")
    print("\nEndpoints:")
    print("  POST   /webhook  - Receive webhooks")
    print("  GET    /history - View webhook history")
    print("  DELETE /history - Clear webhook history")
    print("\nTest with:")
    print(f"  toolkit webhook add http://{host}:{port}/webhook --secret test-secret")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
