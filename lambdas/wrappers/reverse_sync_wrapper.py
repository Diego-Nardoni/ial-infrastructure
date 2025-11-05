import json
from utils.logger import get_logger
from core.drift.reverse_sync import ReverseSync

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Reverse Sync Wrapper"""
    try:
        action = event.get("action", "generate_pr")
        drift = event.get("drift", {})
        reason = event.get("reason", "Drift detected")
        
        logger.info(f"Reverse sync action: {action}")
        
        # Usar ReverseSync existente
        sync = ReverseSync()
        
        if action == "generate_pr":
            result = sync.generate_pr_from_drift(drift, reason)
        else:
            result = sync.discover_and_sync()
        
        logger.info(f"Reverse sync completed: {result}")
        return {
            "status": "OK",
            "action": action,
            "result": result,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Reverse sync failed: {str(e)}")
        raise Exception(f"Reverse sync failed: {str(e)}")
