import json
from utils.logger import get_logger
from mcp.finops.server import FinOpsMCP
from core.decision_ledger import DecisionLedger

logger = get_logger(__name__)

def lambda_handler(event, context):
    """FinOps MCP Wrapper"""
    try:
        phase = event.get("phase")
        stack = event.get("stack")
        region = event.get("region", "us-east-1")
        
        logger.info(f"Running FinOps analysis for phase: {phase}, stack: {stack}")
        
        # Usar FinOpsMCP existente
        finops_mcp = FinOpsMCP()
        result = finops_mcp.analyze_costs(stack, region)
        
        # Log decision
        ledger = DecisionLedger()
        ledger.log_decision(
            phase, 
            mcp="finops", 
            tool="analyze_costs",
            rationale="post-deploy cost analysis", 
            status="SUCCESS",
            metadata={"stack": stack, "estimated_monthly": result.get("estimated_monthly", 0)}
        )
        
        # Save report
        report_path = f"/home/ial/reports/finops/{stack}_budget.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"FinOps analysis completed - monthly: ${result.get('estimated_monthly', 0)}")
        return {
            "status": "OK",
            "phase": phase,
            "stack": stack,
            "estimated_monthly": result.get("estimated_monthly", 0),
            "report_path": report_path,
            "cost_optimization": result.get("optimizations", [])
        }
        
    except Exception as e:
        logger.error(f"FinOps MCP failed: {str(e)}")
        raise Exception(f"FinOps MCP failed: {str(e)}")
