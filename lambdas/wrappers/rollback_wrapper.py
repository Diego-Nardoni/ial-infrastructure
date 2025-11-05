import json
from utils.logger import get_logger
from utils.rollback_manager import RollbackManager

logger = get_logger(__name__)

def lambda_handler(event, context):
    """SAGA Rollback Wrapper"""
    try:
        phase = event.get("phase")
        stack = event.get("stack")
        reason = event.get("reason", "Step Functions SAGA rollback")
        
        logger.info(f"Initiating rollback for phase: {phase}, stack: {stack}")
        
        # Usar RollbackManager existente
        manager = RollbackManager()
        result = manager.rollback_phase(phase, stack, reason)
        
        logger.info(f"Rollback completed: {result}")
        return {
            "status": "OK",
            "phase": phase,
            "stack": stack,
            "rollback_result": result,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise Exception(f"Rollback execution failed: {str(e)}")
