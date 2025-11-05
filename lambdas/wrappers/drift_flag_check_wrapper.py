import json
from utils.logger import get_logger
from core.drift_flag import get_flag

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Drift Flag Check Wrapper"""
    try:
        scope = event.get("scope", "global")
        
        logger.info(f"Checking drift flag for scope: {scope}")
        
        # Usar drift_flag existente
        flag = get_flag(scope)
        state = flag.get("state", "ENABLED")
        
        logger.info(f"Drift flag state: {state}")
        return {
            "state": state,
            "flag": flag,
            "scope": scope
        }
        
    except Exception as e:
        logger.error(f"Drift flag check failed: {str(e)}")
        # Fail-safe: permitir drift detection se flag não disponível
        return {
            "state": "ENABLED",
            "scope": scope,
            "message": "Flag check failed - defaulting to ENABLED"
        }
