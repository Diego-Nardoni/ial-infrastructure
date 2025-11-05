import json
import os
import uuid
import time
from typing import Dict, Any, Optional

class DecisionLedger:
    def __init__(self):
        os.makedirs("reports", exist_ok=True)

    def log(self, phase, mcp, tool, rationale, status, metadata: Optional[Dict[str, Any]] = None):
        entry = {
            "id": str(uuid.uuid4()),
            "ts": int(time.time() * 1000),
            "phase": phase,
            "mcp": mcp,
            "tool": tool,
            "rationale": rationale,
            "status": status
        }
        
        # Add metadata if provided
        if metadata:
            entry["metadata"] = metadata
            
        with open("reports/decisions.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_context(self, phase: str, context_hash: str, snippets_count: int):
        entry = {
            "id": str(uuid.uuid4()),
            "ts": int(time.time() * 1000),
            "type": "RAG_CONTEXT",
            "phase": phase,
            "context_hash": context_hash,
            "snippets_count": snippets_count
        }
        with open("reports/decisions.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_flag_change(self, scope: str, state: str, actor: str, reason: str, 
                       ticket: str = "", duration_hours: int = 0):
        """Log drift flag state changes"""
        self.log(
            phase="drift-control",
            mcp="drift-flag",
            tool="flag_change",
            rationale=f"Changed drift state for {scope} to {state}: {reason}",
            status=state,
            metadata={
                "scope": scope,
                "actor": actor,
                "ticket": ticket,
                "duration_hours": duration_hours,
                "timestamp": time.time()
            }
        )
