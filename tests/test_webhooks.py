from toolkit.webhooks import WebhookManager
import asyncio
import json

async def test_webhook_events():
    # Initialize webhook manager
    webhook_mgr = WebhookManager()
    
    try:
        # Simulate a tool call
        print("\n🛠️  Simulating tool calls...")
        
        # Tool call start
        await webhook_mgr.trigger(
            "tool.call",
            "calculator",
            {
                "inputs": {
                    "x": 10,
                    "y": 5,
                    "operation": "add"
                }
            }
        )
        
        # Tool success
        await webhook_mgr.trigger(
            "tool.success",
            "calculator",
            {
                "inputs": {
                    "x": 10,
                    "y": 5,
                    "operation": "add"
                },
                "outputs": {
                    "result": 15
                }
            }
        )
        
        # Tool error
        await webhook_mgr.trigger(
            "tool.error",
            "calculator",
            {
                "inputs": {
                    "x": 10,
                    "y": 0,
                    "operation": "divide"
                },
                "error": "Division by zero"
            }
        )
        
    finally:
        await webhook_mgr.close()

if __name__ == "__main__":
    print("\n🚀 Starting webhook test...")
    
    # Run test
    asyncio.run(test_webhook_events())
    
    print("\n✨ Test complete! Check webhook server for received events.")
    print("\nTip: View webhook history at http://127.0.0.1:8765/history") 