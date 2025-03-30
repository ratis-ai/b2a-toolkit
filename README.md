# B2A Toolkit 🚀

A lightweight framework to expose any API as an agent-compatible tool. B2A Toolkit makes it easy to create tools that can be used by AI agents, with built-in support for OpenAI's MCP spec, LangChain, and CrewAI.

## Features

### Current Capabilities ✅

- **Tool Definition**
  - Simple decorator-based API
  - Input/output validation
  - Type checking and conversion
  - Built-in documentation support

- **Tool Server**
  - Local HTTP server for tool execution
  - Automatic manifest generation
  - RESTful endpoints for tool invocation
  - Built-in validation and error handling

- **Authentication**
  - OAuth support
  - API key support
  - Configurable scopes
  - Optional auth requirements

- **Framework Support**
  - OpenAI MCP spec compatibility
  - LangChain tool format
  - CrewAI integration

## Installation

```bash
pip install b2a-toolkit
```

## Quick Start

1. Define a tool using the `@define_tool` decorator:

```python
from toolkit import define_tool, ToolAuth

@define_tool(
    name="create_expense",
    description="Creates an expense in the system",
    inputs={
        "amount": "number",
        "category": "string",
        "description": "string",
        "date": "string"
    },
    output_type="object",
    output_description="The created expense object",
    auth=ToolAuth(
        type="oauth",
        required=True,
        scopes=["expenses:write"]
    )
)
def create_expense(amount: float, category: str, description: str, date: str):
    # Your implementation here
    return {"id": "exp_123", "amount": amount, ...}
```

2. Build the tool manifest:
```bash
toolkit build examples/expense_tool.py -o manifest.json
```

3. Start the tool server:
```bash
toolkit serve examples/expense_tool.py
```

This starts a local server with:
- GET `/manifest.json` - Get tool definitions
- POST `/run/<tool_name>` - Execute a tool

4. Use your tools:
```bash
# Get tool manifest
curl http://localhost:8000/manifest.json

# Execute a tool
curl -X POST http://localhost:8000/run/create_expense \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"amount": 100, "category": "office"}}'
```

## Tool Definition

The `@define_tool` decorator takes the following parameters:

- `name`: Name of the tool
- `description`: Description of what the tool does
- `inputs`: Dictionary mapping input parameter names to their types
- `output_type`: Type of the tool's output
- `output_description`: Description of the tool's output
- `auth`: Optional authentication configuration
- `version`: Version of the tool (default: "0.1.0")
- `tags`: Optional list of tags/categories

## CLI Commands

### Build Manifest
```bash
toolkit build <module_path> [--output <output_file>] [--format <json|openapi>]
```

### Start Server
```bash
toolkit serve <module_path> [--host HOST] [--port PORT]
```

### Test Tool
```bash
toolkit test <tool_name> <module_path>
```

## Examples

Check out the `examples/` directory for more examples:

- `expense_tool.py`: A simple expense creation tool
- More examples coming soon...

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 
