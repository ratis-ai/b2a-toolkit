from fastapi import FastAPI, Query
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

    # Serve static files
    dashboard.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # API endpoints
    @dashboard.get("/api/logs")
    async def get_logs(
        tool: str = None,
        status: str = None,
        limit: int = Query(default=50, le=100),
        offset: int = 0
    ):
        """Fetch paginated logs with filtering"""
        logs = logger.get_logs(tool_name=tool, limit=limit)
        
        # Filter by status if specified
        if status == "success":
            logs = [log for log in logs if not log.error]
        elif status == "error":
            logs = [log for log in logs if log.error]
            
        return [log.to_dict() for log in logs]

    @dashboard.get("/", response_class=HTMLResponse)
    async def home():
        """Serve the dashboard home page"""
        with open(static_dir / "index.html") as f:
            return f.read()

    return dashboard 