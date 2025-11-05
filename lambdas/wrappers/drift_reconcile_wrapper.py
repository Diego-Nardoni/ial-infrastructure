import json
from utils.logger import get_logger
from lambdas.drift_reconciler import reconcile_drift

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Drift Reconcile Wrapper"""
    try:
        scope = event.get("scope", "global")
        drift_details = event.get("drift", {}).get("Payload", {}).get("details", {})
        
        logger.info(f"Reconciling drift for scope: {scope}")
        
        # Usar drift_reconciler existente
        result = reconcile_drift(scope, drift_details)
        
        logger.info(f"Drift reconciliation completed: {result}")
        return {
            "status": "OK",
            "scope": scope,
            "reconciled": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Drift reconciliation failed: {str(e)}")
        raise Exception(f"Drift reconciliation failed: {str(e)}")
