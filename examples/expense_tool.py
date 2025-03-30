"""
Example tool for expense management
"""
from datetime import datetime
from typing import Dict
from toolkit.core import define_tool, registry  # Import registry

@define_tool(
    name="create_expense",
    description="Creates an expense in the system",
    inputs={
        "amount": "number",
        "category": "string",
        "description": "string",
        "date": "string"
    },
    output_description="The created expense object",
    auth={
        "required": True,
        "scopes": ["expenses:write"]
    }
)
async def create_expense(
    amount: float,
    category: str,
    description: str,
    date: str
) -> Dict[str, any]:
    """
    Creates a new expense entry in the system.
    
    Args:
        amount: The expense amount
        category: Category of the expense (e.g., "travel", "food", "office")
        description: Detailed description of the expense
        date: Date of the expense in YYYY-MM-DD format
    
    Returns:
        Dict containing the created expense details
    """
    # This is a mock implementation
    try:
        # Validate date format
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        
        # Mock response
        expense = {
            "id": "exp_123",  # Mock ID
            "amount": amount,
            "category": category,
            "description": description,
            "date": date,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        return expense
        
    except ValueError as e:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD") from e

# Make sure the tool is registered when the module is imported
tool = registry.get_tool("create_expense")
if not tool:
    raise RuntimeError("Tool 'create_expense' was not properly registered") 