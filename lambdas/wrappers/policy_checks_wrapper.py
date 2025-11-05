import subprocess
import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

def lambda_handler(event, context):
    """OPA/Conftest Policy Checks Wrapper"""
    try:
        phase = event.get("phase")
        
        logger.info(f"Running OPA policy checks for phase: {phase}")
        
        # Run conftest
        result = subprocess.run(
            ["conftest", "test", "/home/ial/rules/", "--output", "json"],
            capture_output=True,
            text=True,
            cwd="/home/ial"
        )
        
        if result.returncode == 0:
            logger.info("OPA policy checks passed")
            return {"opa": "PASS", "phase": phase}
        else:
            logger.error(f"OPA policy checks failed: {result.stderr}")
            raise Exception(f"OPA policy validation failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"OPA policy checks failed: {str(e)}")
        raise Exception(f"OPA policy checks failed: {str(e)}")

def guard_handler(event, context):
    """CFN-Guard Policy Checks Handler"""
    try:
        phase = event.get("phase")
        
        logger.info(f"Running CFN-Guard checks for phase: {phase}")
        
        # Run cfn-guard
        result = subprocess.run(
            ["cfn-guard", "validate", "-r", "/home/ial/rules/", "-d", f"/home/ial/phases/{phase}/"],
            capture_output=True,
            text=True,
            cwd="/home/ial"
        )
        
        if result.returncode == 0:
            logger.info("CFN-Guard checks passed")
            return {"cfn-guard": "PASS", "phase": phase}
        else:
            logger.error(f"CFN-Guard checks failed: {result.stderr}")
            raise Exception(f"CFN-Guard validation failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"CFN-Guard checks failed: {str(e)}")
        raise Exception(f"CFN-Guard checks failed: {str(e)}")
