import json
from utils.logger import get_logger
from mcp.well_architected import WellArchitectedMCP
from core.decision_ledger import DecisionLedger

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Well-Architected MCP Wrapper"""
    try:
        phase = event.get("phase")
        stack = event.get("stack")
        region = event.get("region", "us-east-1")
        
        logger.info(f"Running WA review for phase: {phase}, stack: {stack}")
        
        # Usar WellArchitectedMCP existente
        wa_mcp = WellArchitectedMCP()
        result = wa_mcp.review_workload(stack, region)
        
        # Log decision
        ledger = DecisionLedger()
        ledger.log_decision(
            phase, 
            mcp="well-architected", 
            tool="review_workload",
            rationale="post-deploy WA assessment", 
            status="SUCCESS",
            metadata={"stack": stack, "score": result.get("score", 0)}
        )
        
        # Save report
        report_path = f"/home/ial/reports/well-architected/{stack}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"WA review completed - score: {result.get('score', 0)}")
        return {
            "status": "OK",
            "phase": phase,
            "stack": stack,
            "wa_score": result.get("score", 0),
            "report_path": report_path,
            "recommendations": result.get("recommendations", [])
        }
        
    except Exception as e:
        logger.error(f"WA MCP failed: {str(e)}")
        raise Exception(f"Well-Architected MCP failed: {str(e)}")
