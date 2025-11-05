import json
from utils.logger import get_logger
from core.drift.drift_detector import DriftDetector

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Drift Detection Wrapper"""
    try:
        scope = event.get("scope", "global")
        region = event.get("region", "us-east-1")
        
        logger.info(f"Detecting drift for scope: {scope} in region: {region}")
        
        # Usar DriftDetector existente
        detector = DriftDetector()
        result = detector.detect_drift(scope, region)
        
        detected = result.get("drift_detected", False)
        safe = result.get("safe_to_reconcile", False)
        
        logger.info(f"Drift detection result - detected: {detected}, safe: {safe}")
        return {
            "detected": detected,
            "safe": safe,
            "scope": scope,
            "region": region,
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Drift detection failed: {str(e)}")
        raise Exception(f"Drift detection failed: {str(e)}")
