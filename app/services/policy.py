import time
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore
from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: str
    rules_fired: list[str]


class PolicyEngine:
    def __init__(self, policies_path: Path):
        self.policies_path = policies_path
        self.policies = self._load_policies()
        self._last_loaded = time.time()

    def _load_policies(self) -> dict[str, dict[str, Any]]:
        policies: dict[str, dict[str, Any]] = {}
        for file in self.policies_path.glob("*.yaml"):
            with open(file, encoding="utf-8") as f:
                policies[file.stem] = yaml.safe_load(f) or {}
        return policies

    def _maybe_reload(self) -> None:
        newest = max(
            (f.stat().st_mtime for f in self.policies_path.glob("*.yaml")),
            default=self._last_loaded,
        )
        if newest > self._last_loaded:
            self.policies = self._load_policies()
            self._last_loaded = time.time()

    @staticmethod
    def _classify_intents(query: str) -> list[str]:
        q = query.lower()
        intents = []
        if any(k in q for k in ["pii", "ssn", "social security", "secret", "confidential"]):
            intents.append("sensitive_data")
        if any(k in q for k in ["policy", "compliance", "regulation", "standard"]):
            intents.append("policy")
        if "calculate" in q or any(sym in q for sym in ["+", "-", "*", "/"]):
            intents.append("math")
        if not intents:
            intents.append("general")
        return intents

    def _role_blocked(self, policy: dict[str, Any], role: str) -> bool:
        denied_roles = cast(list[str], policy.get("denied_roles", []) or [])
        if role in denied_roles:
            return True
        allowed_roles = cast(list[str], policy.get("allowed_roles") or [])
        if allowed_roles and role not in allowed_roles:
            return True
        return False

    def evaluate(self, role: str, query: str, experts: list[str]) -> PolicyDecision:
        self._maybe_reload()
        intents = self._classify_intents(query)
        rules_fired: list[str] = []
        decision = "allow"

        for name, policy in self.policies.items():
            enforce = policy.get("enforce_always", False)
            keywords = policy.get("applies_keywords", [])
            applies = enforce or any(k in query.lower() for k in keywords)

            required_intents = policy.get("required_intents", [])
            if required_intents and not any(i in intents for i in required_intents):
                applies = False

            if self._role_blocked(policy, role):
                applies = True

            disallowed_intents = policy.get("disallowed_intents", [])
            if any(intent in intents for intent in disallowed_intents):
                applies = True

            if not applies:
                continue

            if self._role_blocked(policy, role):
                decision = "deny"
                rules_fired.append(f"{name}:role-deny")

            if any(intent in intents for intent in disallowed_intents):
                decision = "deny"
                rules_fired.append(f"{name}:intent-deny")

            allowed_experts = cast(list[str], policy.get("allowed_experts") or [])
            if allowed_experts:
                disallowed = [e for e in experts if e not in allowed_experts]
                if disallowed:
                    decision = "deny"
                    rules_fired.append(f"{name}:expert-deny")

            restricted_tools = cast(list[str], policy.get("restricted_tools") or [])
            if role == "user" and restricted_tools:
                blocked = [e for e in experts if e in restricted_tools]
                if blocked:
                    decision = "deny"
                    rules_fired.append(f"{name}:tool-block")

        return PolicyDecision(decision=decision, rules_fired=rules_fired)
