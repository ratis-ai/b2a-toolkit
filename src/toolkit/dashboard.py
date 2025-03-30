from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from .logging import ToolLogger

def create_dashboard() -> FastAPI:
    """Create and configure the dashboard FastAPI application"""
    dashboard = FastAPI(title="B2A Toolkit Dashboard")
    logger = ToolLogger()

    # Get the absolute path to the static directory
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    # API endpoints
    @dashboard.get("/api/logs")
    async def get_logs(tool: str = None, limit: int = 50, offset: int = 0):
        """Fetch paginated logs with optional filtering"""
        logs = logger.get_logs(tool_name=tool, limit=limit)
        return [log.to_dict() for log in logs]

    @dashboard.get("/", response_class=HTMLResponse)
    async def home():
        """Serve the dashboard home page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>B2A Toolkit Dashboard</title>
            <style>
                body { font-family: system-ui, sans-serif; margin: 2rem; }
                .logs { margin-top: 2rem; }
                .log-entry { border: 1px solid #eee; padding: 1rem; margin: 1rem 0; }
            </style>
        </head>
        <body>
            <h1>B2A Toolkit Dashboard</h1>
            <div class="logs">
                <h2>Recent Tool Calls</h2>
                <div id="logs-list"></div>
            </div>
            <script>
                async function fetchLogs() {
                    const response = await fetch('/api/logs');
                    const logs = await response.json();
                    const logsHtml = logs.map(log => `
                        <div class="log-entry">
                            <h3>${log.tool_name}</h3>
                            <p>Time: ${new Date(log.timestamp).toLocaleString()}</p>
                            <p>Duration: ${log.duration_ms}ms</p>
                            <pre>Inputs: ${JSON.stringify(log.inputs, null, 2)}</pre>
                            ${log.outputs ? 
                                `<pre>Outputs: ${JSON.stringify(log.outputs, null, 2)}</pre>` : 
                                `<p style="color: red">Error: ${log.error}</p>`}
                        </div>
                    `).join('');
                    document.getElementById('logs-list').innerHTML = logsHtml;
                }
                
                // Fetch logs initially and every 5 seconds
                fetchLogs();
                setInterval(fetchLogs, 5000);
            </script>
        </body>
        </html>
        """

    return dashboard 