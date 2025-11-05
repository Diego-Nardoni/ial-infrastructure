import os
import boto3
import json
from utils.logger import get_logger

logger = get_logger(__name__)
ssm = boto3.client("ssm")

def lambda_handler(event, context):
    """Circuit Breaker via SSM Parameters"""
    try:
        # Verificar estado do circuit breaker
        state = ssm.get_parameter(Name="/ial/circuit_breaker/state")["Parameter"]["Value"]
        
        if state == "open":
            retry_after = int(ssm.get_parameter(Name="/ial/circuit_breaker/retry_after_sec")["Parameter"]["Value"])
            logger.warning(f"Circuit breaker OPEN - retry after {retry_after}s")
            return {
                "circuit": "OPEN",
                "retry_after": retry_after,
                "message": "Circuit breaker is open - blocking execution"
            }
        
        # Verificar max inflight
        max_inflight = int(ssm.get_parameter(Name="/ial/circuit_breaker/max_inflight")["Parameter"]["Value"])
        
        logger.info(f"Circuit breaker {state} - max_inflight: {max_inflight}")
        return {
            "circuit": "OK",
            "state": state,
            "max_inflight": max_inflight
        }
        
    except Exception as e:
        logger.error(f"Circuit breaker check failed: {str(e)}")
        # Fail-safe: permitir execução se SSM não disponível
        return {
            "circuit": "OK",
            "state": "closed",
            "message": "Circuit breaker check failed - allowing execution"
        }
