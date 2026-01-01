from typing import List, Dict, Tuple
from app.services.experts import BaseExpert, ExpertSmall, ExpertLarge, ToolExpert, RetrieverExpert


class RouterDecision:
    def __init__(self, chosen: List[str], reason_codes: List[str]):
        self.chosen = chosen
        self.reason_codes = reason_codes


def build_router(retriever: RetrieverExpert) -> Tuple[List[BaseExpert], RouterDecision]:
    experts: List[BaseExpert] = [ExpertSmall(), ExpertLarge(), ToolExpert(), retriever]
    decision = RouterDecision([e.name for e in experts], ["all-enabled"])
    return experts, decision


def choose_experts(query: str, budget_latency_ms: int, budget_cost_units: int, experts: List[BaseExpert]) -> RouterDecision:
    chosen = []
    reasons = []
    if "calculate" in query:
        chosen.append("tool_calculator")
        reasons.append("math-detected")
    if budget_latency_ms < 500:
        chosen.append("expert_small")
        reasons.append("low-latency")
    else:
        chosen.append("expert_large")
        reasons.append("quality")
    if "docs" in query or "policy" in query:
        chosen.append("retriever")
        reasons.append("info-retrieval")
    # deduplicate
    chosen = list(dict.fromkeys(chosen))
    return RouterDecision(chosen, reasons)
