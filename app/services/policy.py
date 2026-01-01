import yaml
from typing import List
from pydantic import BaseModel
from pathlib import Path


class PolicyDecision(BaseModel):
    decision: str
    rules_fired: List[str]


class PolicyEngine:
    def __init__(self, policies_path: Path):
        self.policies_path = policies_path
        self.policies = self._load_policies()

    def _load_policies(self):
        policies = {}
        for file in self.policies_path.glob("*.yaml"):
            with open(file, "r", encoding="utf-8") as f:
                policies[file.stem] = yaml.safe_load(f)
        return policies

    def evaluate(self, role: str, query: str, experts: List[str]) -> PolicyDecision:
        rules_fired: List[str] = []
        decision = "allow"
        # basic allow/deny based on role and disallowed intents
        for name, policy in self.policies.items():
            disallowed_intents = policy.get("disallowed_intents", [])
            if any(intent in query.lower() for intent in disallowed_intents):
                decision = "deny"
                rules_fired.append(f"{name}:intent-deny")
            if role == "user" and policy.get("restricted_tools"):
                blocked = [e for e in experts if e in policy.get("restricted_tools")]
                if blocked:
                    decision = "deny"
                    rules_fired.append(f"{name}:tool-block")
        return PolicyDecision(decision=decision, rules_fired=rules_fired)
