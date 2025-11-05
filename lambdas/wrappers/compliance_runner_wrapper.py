import json
from utils.logger import get_logger
from compliance.ial_config_rules import IALConfigRules
from core.decision_ledger import DecisionLedger

logger = get_logger(__name__)

def lambda_handler(event, context):
    """Compliance Runner Wrapper"""
    try:
        phase = event.get("phase")
        stack = event.get("stack")
        region = event.get("region", "us-east-1")
        
        logger.info(f"Running compliance checks for phase: {phase}, stack: {stack}")
        
        # Usar IALConfigRules existente
        compliance = IALConfigRules()
        result = compliance.run_compliance_checks(stack, region)
        
        compliance_score = result.get("compliance_percentage", 0)
        
        # Log decision
        ledger = DecisionLedger()
        ledger.log_decision(
            phase, 
            mcp="compliance", 
            tool="run_compliance_checks",
            rationale="post-deploy compliance validation", 
            status="SUCCESS" if compliance_score >= 90 else "WARNING",
            metadata={"stack": stack, "compliance_score": compliance_score}
        )
        
        # Save report
        report_path = f"/home/ial/reports/compliance/{stack}_compliance.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Compliance check completed - score: {compliance_score}%")
        return {
            "status": "OK",
            "phase": phase,
            "stack": stack,
            "compliance_score": compliance_score,
            "report_path": report_path,
            "violations": result.get("violations", [])
        }
        
    except Exception as e:
        logger.error(f"Compliance runner failed: {str(e)}")
        raise Exception(f"Compliance runner failed: {str(e)}")
