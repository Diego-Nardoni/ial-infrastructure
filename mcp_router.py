from core.mcp_registry import MCPRegistry
from core.decision_ledger import DecisionLedger

class MCPRouter:
    def __init__(self):
        self.registry = MCPRegistry()
        self.ledger = DecisionLedger()

    def route(self, domain, tool, context):
        candidates = []

        for name in self.registry.list():
            tools = self.registry.list_tools(name)
            if tool in tools:
                score = 1
                if domain in name:
                    score += 2
                candidates.append((score, name))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        selected = candidates[0][1]

        self.ledger.log(
            phase=context.get("phase", "unknown"),
            mcp=selected,
            tool=tool,
            rationale=f"route(domain={domain}, tool={tool})",
            status="ROUTED"
        )

        return self.registry.get(selected)
