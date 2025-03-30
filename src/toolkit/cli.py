"""
Command-line interface for ToolPilot
"""
import json
import sys
from pathlib import Path
from typing import Optional
import click
from .core import ToolRegistry
import inspect
import uvicorn
from .server import app, load_tools_from_path

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
        # Import the module dynamically
        module_path = Path(module_path)
        sys.path.append(str(module_path.parent))
        module = __import__(module_path.stem)
        
        # Find all tools in the module
        registry = ToolRegistry()
        for name, obj in inspect.getmembers(module):
            if hasattr(obj, 'tool'):
                registry.register(obj.tool)
        
        # Generate manifest
        manifest = registry.list_tools()
        
        # Output the manifest
        if output:
            output_path = Path(output)
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
            elif format == 'openapi':
                # TODO: Implement OpenAPI conversion
                click.echo("OpenAPI format not yet implemented")
        else:
            click.echo(json.dumps(manifest, indent=2))
            
    except Exception as e:
        click.echo(f"Error building manifest: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('tool_name')
@click.argument('module_path', type=click.Path(exists=True))
def test(tool_name: str, module_path: str):
    """Test a specific tool"""
    try:
        # Import the module and find the tool
        module_path = Path(module_path)
        sys.path.append(str(module_path.parent))
        module = __import__(module_path.stem)
        
        tool = None
        for name, obj in inspect.getmembers(module):
            if hasattr(obj, 'tool') and obj.tool.metadata.name == tool_name:
                tool = obj.tool
                break
                
        if not tool:
            click.echo(f"Tool '{tool_name}' not found in module", err=True)
            sys.exit(1)
            
        # TODO: Implement interactive testing
        click.echo(f"Testing tool: {tool.metadata.name}")
        click.echo(f"Description: {tool.metadata.description}")
        click.echo("\nInput parameters:")
        for input_param in tool.metadata.inputs:
            click.echo(f"- {input_param.name}: {input_param.type}")
            
    except Exception as e:
        click.echo(f"Error testing tool: {e}", err=True)
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

if __name__ == '__main__':
    cli() 