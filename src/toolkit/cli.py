"""
Command-line interface for ToolPilot
"""
import json
import sys
from pathlib import Path
from typing import Optional
import click
from .core import ToolRegistry
from inspect import getmembers
import uvicorn
from .server import app, load_tools_from_path
from .logging import ToolLogger
from .dashboard import create_dashboard
import importlib.util

def _load_module(module_path: Path) -> object:
    """Load a Python module from a file path using importlib"""
    try:
        spec = importlib.util.spec_from_file_location(module_path.stem, str(module_path))
        if spec is None:
            raise ImportError(f"Could not load module spec from {module_path}")
            
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ImportError(f"Could not load module loader from {module_path}")
            
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        raise ImportError(f"Failed to load module {module_path}: {e}")

@click.group()
def cli():
    """ToolPilot CLI - Build and manage agent-compatible tools"""
    pass

@cli.command()
@click.argument('module_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for the tool manifest')
@click.option('--format', '-f', type=click.Choice(['json', 'openapi']), default='json',
              help='Output format for the tool manifest')
def build(module_path: str, output: Optional[str], format: str):
    """Build a tool manifest from a Python module"""
    try:
        click.echo(f"🔍 Loading tools from {module_path}")
        
        # Load module and register tools
        module = _load_module(Path(module_path))
        registry = ToolRegistry()
        
        tools_found = []
        for name, obj in getmembers(module):
            if hasattr(obj, 'tool'):
                registry.register(obj.tool)
                tools_found.append(obj.tool.metadata.name)
        
        if not tools_found:
            click.echo("⚠️  No tools found in module")
            sys.exit(1)
            
        click.echo(f"✨ Found {len(tools_found)} tools: {', '.join(tools_found)}")
        
        # Generate and output manifest
        manifest = registry.list_tools()
        if output:
            output_path = Path(output)
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                click.echo(f"📝 Manifest written to: {output_path}")
                click.echo(f"   Format: {format}")
                click.echo(f"   Size: {len(json.dumps(manifest))} bytes")
            else:
                click.echo("⚠️  OpenAPI format not yet implemented")
        else:
            click.echo("\n📋 Tool Manifest:")
            click.echo(json.dumps(manifest, indent=2))
            
        click.echo("\n✅ Build completed successfully!")
            
    except Exception as e:
        click.echo(f"❌ Error building manifest: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('tool_name')
@click.argument('module_path', type=click.Path(exists=True))
def test(tool_name: str, module_path: str):
    """Test a specific tool"""
    try:
        click.echo(f"🔍 Loading module from {module_path}")
        
        # Load module and find tool
        module = _load_module(Path(module_path))
        
        click.echo(f"🔎 Looking for tool '{tool_name}'")
        tool = None
        for name, obj in getmembers(module):
            if hasattr(obj, 'tool') and obj.tool.metadata.name == tool_name:
                tool = obj.tool
                break
                
        if not tool:
            click.echo(f"❌ Tool '{tool_name}' not found in module", err=True)
            sys.exit(1)
            
        # Display tool information
        click.echo("\n📋 Tool Details:")
        click.echo(f"  Name: {tool.metadata.name}")
        click.echo(f"  Description: {tool.metadata.description}")
        
        click.echo("\n📥 Input Parameters:")
        if tool.metadata.inputs:
            for input_param in tool.metadata.inputs:
                click.echo(f"  • {input_param.name} ({input_param.type})")
                if hasattr(input_param, 'description') and input_param.description:
                    click.echo(f"    {input_param.description}")
        else:
            click.echo("  No input parameters required")
            
        click.echo("\n📤 Output:")
        if hasattr(tool.metadata, 'output_description'):
            click.echo(f"  Description: {tool.metadata.output_description}")
            
        if hasattr(tool.metadata, 'auth') and tool.metadata.auth:
            click.echo("\n🔒 Authentication:")
            click.echo(f"  Required: {tool.metadata.auth.required}")
            if tool.metadata.auth.scopes:
                click.echo(f"  Scopes: {', '.join(tool.metadata.auth.scopes)}")
            
        click.echo("\n✅ Tool validation successful!")
            
    except Exception as e:
        click.echo(f"\n❌ Error testing tool: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('module_path', type=click.Path(exists=True))
@click.option('--host', default="127.0.0.1", help="Host to bind to")
@click.option('--port', default=8000, help="Port to bind to")
def serve(module_path: str, host: str, port: int):
    """Start a local server to execute tools"""
    try:
        load_tools_from_path(module_path)
        click.echo(f"Loading tools from {module_path}")
        click.echo(f"Server running at http://{host}:{port}")
        click.echo("Available endpoints:")
        click.echo("  - GET  /manifest.json")
        click.echo("  - POST /run/<tool_name>")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        click.echo(f"Error starting server: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--tool', help='Filter logs by tool name')
@click.option('--limit', default=10, help='Number of logs to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output in real-time')
@click.option('--format', type=click.Choice(['text', 'json']), default='text',
              help='Output format for logs')
def logs(tool: str, limit: int, follow: bool, format: str):
    """View tool execution logs"""
    try:
        logger = ToolLogger()
        
        if follow:
            click.echo("Watching for new tool calls... (Ctrl+C to exit)")
            try:
                for log in logger.watch_logs(tool_name=tool):
                    _display_log(log, format)
            except KeyboardInterrupt:
                click.echo("\nStopped watching logs")
                return
        else:
            logs = logger.get_logs(tool_name=tool, limit=limit)
            if not logs:
                if tool:
                    click.echo(f"No logs found for tool '{tool}'")
                else:
                    click.echo("No logs found. Run some tools first!")
                click.echo("\nTip: Use --follow (-f) to watch for new logs")
                return
                
            for log in logs:
                _display_log(log, format)
                
    except Exception as e:
        click.echo(f"Error viewing logs: {str(e)}", err=True)
        sys.exit(1)

def _display_log(log, format='text'):
    """Helper function to display a single log entry"""
    if format == 'json':
        click.echo(json.dumps(log.to_dict(), indent=2))
    else:
        # Text format
        status = "✓" if log.outputs else "✗"
        click.echo(f"[{log.timestamp}] {status} {log.tool_name} ({log.duration_ms:.0f}ms)")
        click.echo(f"  ID: {log.call_id}")
        click.echo(f"  Inputs: {json.dumps(log.inputs, indent=2)}")
        if log.outputs:
            click.echo(f"  Outputs: {json.dumps(log.outputs, indent=2)}")
        if log.error:
            click.echo(f"  Error: {log.error}", err=True)
        click.echo("")

@cli.command()
@click.option('--host', default="127.0.0.1", help="Host to bind to")
@click.option('--port', default=8001, help="Port to bind to")
def dashboard(host: str, port: int):
    """Start the web dashboard for tool monitoring"""
    try:
        click.echo(f"🚀 Starting dashboard at http://{host}:{port}")
        click.echo("\n📊 Available views:")
        click.echo("  • /           (Dashboard home)")
        click.echo("  • /logs       (Live log viewer)")
        click.echo("  • /analytics  (Usage analytics)")
        
        dashboard_app = create_dashboard()
        uvicorn.run(dashboard_app, host=host, port=port)
    except Exception as e:
        click.echo(f"\n❌ Error starting dashboard: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('tool_name')
@click.option('--last', default=5, help="Number of recent calls to show")
def inspect(tool_name: str, last: int):
    """Inspect recent calls to a specific tool"""
    try:
        logger = ToolLogger()
        calls = logger.get_logs(tool_name=tool_name, limit=last)
        
        if not calls:
            click.echo(f"No recent calls found for tool '{tool_name}'")
            return
            
        click.echo(f"Recent calls to {tool_name}:")
        for call in calls:
            _display_log(call)
            
    except Exception as e:
        click.echo(f"Error inspecting tool: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli() 