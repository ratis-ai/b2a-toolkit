"""
Example tool that creates an expense in a system
"""
import requests
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
    output_description="The created expense object",
    auth=ToolAuth(
        type="oauth",
        required=True,
        scopes=["expenses:write"]
    ),
    tags=["expenses", "finance"]
)
def create_expense(amount: float, category: str, description: str, date: str):
    """
    Create a new expense in the system
    
    Args:
        amount: The expense amount
        category: The expense category
        description: Description of the expense
        date: Date of the expense (ISO format)
        
    Returns:
        The created expense object
    """
    # This is a mock implementation
    # In a real tool, you would make an actual API call
    return {
        "id": "exp_123",
        "amount": amount,
        "category": category,
        "description": description,
        "date": date,
        "status": "created"
    } 