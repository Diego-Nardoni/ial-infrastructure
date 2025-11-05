import json
from utils.logger import get_logger
from scripts.reconcile import execute_changeset

logger = get_logger(__name__)

def lambda_handler(event, context):
    """ExecuteChangeSet Wrapper"""
    try:
        stack = event.get("stack")
        changeset_name = event.get("changeset_name")
        
        logger.info(f"Applying changeset: {changeset_name} for stack: {stack}")
        
        # Usar função de reconcile existente
        result = execute_changeset(stack, changeset_name)
        
        logger.info(f"Apply completed: {result}")
        return {
            "status": "OK",
            "stack": stack,
            "changeset": changeset_name,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Apply failed: {str(e)}")
        raise Exception(f"Apply execution failed: {str(e)}")
