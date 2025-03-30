from functools import wraps
import time
from .logging import ToolLogger

logger = ToolLogger()

def define_tool(**tool_config):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # Log the incoming call
                inputs = kwargs
                
                # Execute the tool
                result = await func(*args, **kwargs)
                
                # Calculate duration and log success
                duration_ms = (time.time() - start_time) * 1000
                logger.log_call(
                    tool_name=tool_config['name'],
                    inputs=inputs,
                    outputs=result,
                    duration_ms=duration_ms,
                    agent_metadata=kwargs.get('_agent_metadata')
                )
                
                return result
                
            except Exception as e:
                # Log error case
                duration_ms = (time.time() - start_time) * 1000
                logger.log_call(
                    tool_name=tool_config['name'],
                    inputs=kwargs,
                    error=str(e),
                    duration_ms=duration_ms,
                    agent_metadata=kwargs.get('_agent_metadata')
                )
                raise
                
        return wrapper
    return decorator 