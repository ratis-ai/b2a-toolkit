from functools import wraps
import time
from .logging import ToolLogger
from typing import Dict, Any, Optional

logger = ToolLogger()

def define_tool(**tool_config):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            call_id = None
            inputs = kwargs
            
            try:
                # Trigger pre-execution webhook if available
                if hasattr(args[0], 'webhook_manager'):
                    await args[0].webhook_manager.trigger('tool.call', 
                        tool_config['name'], 
                        {'inputs': inputs}
                    )
                
                # Execute the tool
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log the successful call
                call_id = logger.log_call(
                    tool_name=tool_config['name'],
                    inputs=inputs,
                    outputs=result,
                    duration_ms=duration_ms,
                    agent_metadata=kwargs.get('_agent_metadata')
                )
                
                # Trigger success webhook if available
                if hasattr(args[0], 'webhook_manager'):
                    await args[0].webhook_manager.trigger('tool.success',
                        tool_config['name'],
                        {
                            'call_id': call_id,
                            'inputs': inputs,
                            'outputs': result,
                            'duration_ms': duration_ms
                        }
                    )
                
                return result
                
            except Exception as e:
                # Calculate duration for error case
                duration_ms = (time.time() - start_time) * 1000
                
                # Log the error
                call_id = logger.log_call(
                    tool_name=tool_config['name'],
                    inputs=kwargs,
                    error=str(e),
                    duration_ms=duration_ms,
                    agent_metadata=kwargs.get('_agent_metadata')
                )
                
                # Trigger error webhook if available
                if hasattr(args[0], 'webhook_manager'):
                    await args[0].webhook_manager.trigger('tool.error',
                        tool_config['name'],
                        {
                            'call_id': call_id,
                            'inputs': inputs,
                            'error': str(e),
                            'duration_ms': duration_ms
                        }
                    )
                raise
                
        return wrapper
    return decorator 