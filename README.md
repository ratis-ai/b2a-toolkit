# B2A Toolkit 🚀

A lightweight framework to expose any API as an agent-compatible tool. B2A Toolkit makes it easy to create tools that can be used by AI agents, with built-in support for OpenAI's MCP spec, LangChain, and CrewAI.

## Features

- 🎯 Simple decorator-based tool definition
- 🔒 Built-in authentication handling
- 📝 Automatic tool manifest generation
- 🔄 Support for multiple agent frameworks
- 🛠️ CLI for building and testing tools

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

3. Test the tool:

```bash
toolkit test create_expense examples/expense_tool.py
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

## Authentication

ToolPilot supports different authentication types:

- OAuth
- API Key
- None (for public APIs)

Example OAuth configuration:

```python
auth = ToolAuth(
    type="oauth",
    required=True,
    scopes=["expenses:write"]
)
```

## CLI Commands

### Build Manifest

```bash
toolkit build <module_path> [--output <output_file>] [--format <json|openapi>]
```

### Test Tool

```bash
toolkit test <tool_name> <module_path>
```
## Examples

Check out the `examples/` directory for more examples:

- `expense_tool.py`: A simple expense creation tool
- More examples coming soon...

## Current Capabilities

- **Tool Definition**
  - Simple decorator-based API
  - Input/output validation
  - Type checking and conversion
  - Built-in documentation support

- **Authentication**
  - OAuth support
  - API key support
  - Configurable scopes
  - Optional auth requirements

- **Manifest Generation**
  - JSON format export
  - CLI tool for building manifests
  - Validation of tool definitions
  - Support for metadata and tags

- **Agent Framework Support**
  - OpenAI MCP spec compatibility
  - LangChain tool format
  - CrewAI integration

## Coming Soon 🚀

- **Enhanced Manifest Support**
  - OpenAPI format export
  - GraphQL schema generation
  - Custom format plugins
  - Schema validation

- **Hosted Dashboard**
  - Tool registry and discovery
  - Live testing interface
  - Usage analytics
  - Error tracking

- **Advanced Features**
  - Rate limiting and quotas
  - Retry handling
  - Error recovery
  - Request/response logging

- **Enterprise Features**
  - Team management
  - Access control
  - Audit logging
  - Custom authentication providers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 
