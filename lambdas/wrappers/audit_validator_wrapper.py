import json
from utils.logger import get_logger
from core.audit_validator import compare_and_report

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Creation Completeness Audit Wrapper"""
    try:
        region = event.get("region", "us-east-1")
        phase = event.get("phase")
        
        logger.info(f"Running audit validation for phase: {phase} in region: {region}")
        
        # Usar audit_validator existente
        report = compare_and_report(region=region, phase=phase)
        
        completeness = report.get("completeness", 0)
        if completeness < 100:
            logger.error(f"Creation Completeness < 100%: {completeness}%")
            raise Exception(f"Creation Completeness failed: {completeness}%")
        
        logger.info(f"Audit validation passed: {completeness}%")
        return {
            "status": "OK",
            "completeness": completeness,
            "report": report,
            "phase": phase
        }
        
    except Exception as e:
        logger.error(f"Audit validation failed: {str(e)}")
        raise Exception(f"Audit validation failed: {str(e)}")
