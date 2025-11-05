import json
from utils.logger import get_logger
from scripts.phase_manager import PhaseManager

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Plan/ChangeSet Wrapper"""
    try:
        phase = event.get("phase")
        region = event.get("region", "us-east-1")
        
        logger.info(f"Planning phase: {phase} in region: {region}")
        
        # Usar PhaseManager existente
        manager = PhaseManager()
        result = manager.plan_phase(phase, region)
        
        logger.info(f"Plan completed: {result}")
        return {
            "status": "OK",
            "phase": phase,
            "plan": result,
            "region": region
        }
        
    except Exception as e:
        logger.error(f"Plan failed: {str(e)}")
        raise Exception(f"Plan execution failed: {str(e)}")
