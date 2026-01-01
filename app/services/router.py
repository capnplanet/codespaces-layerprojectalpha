from dataclasses import dataclass

from app.services.experts import BaseExpert, ExpertLarge, ExpertSmall, RetrieverExpert, ToolExpert


@dataclass
class RouterDecision:
    chosen: list[str]
    reason_codes: list[str]
    estimated_latency_ms: int
    estimated_cost_units: int
    fallbacks: list[str]


@dataclass
class ExpertProfile:
    name: str
    cost: int
    latency_ms: int
    quality: float
    score: float
    reasons: list[str]


class Router:
    def __init__(self, experts: list[BaseExpert]):
        self.experts = experts
        self.quality_priors: dict[str, float] = {
            "expert_small": 0.55,
            "expert_large": 0.78,
            "tool_calculator": 0.70,
            "retriever": 0.65,
        }

    def _detect_features(self, query: str) -> dict[str, bool]:
        q = query.lower()
        return {
            "math": "calculate" in q,
            "info": any(k in q for k in ["docs", "document", "policy", "evidence"]),
            "low_latency": len(q) < 80,
        }

    def _profile(
        self,
        expert: BaseExpert,
        features: dict[str, bool],
        budget_latency_ms: int,
        budget_cost_units: int,
    ) -> ExpertProfile:
        expected_latency = int(sum(expert.latency_range) / 2)
        base_quality = self.quality_priors.get(expert.name, 0.5)
        reasons: list[str] = []
        score = base_quality

        if features["math"] and expert.name == "tool_calculator":
            score += 0.5
            reasons.append("math-boost")
        if features["info"] and expert.name == "retriever":
            score += 0.3
            reasons.append("retrieval-boost")
        if not features["low_latency"] and expert.name == "expert_large":
            score += 0.15
            reasons.append("quality-priority")
        if features["low_latency"] and expert.name == "expert_large":
            score -= 0.15
            reasons.append("latency-penalty")

        latency_penalty = (expected_latency / max(budget_latency_ms, 1)) * 0.4
        cost_penalty = (expert.cost_per_call / max(budget_cost_units, 1)) * 0.3
        score -= latency_penalty + cost_penalty

        return ExpertProfile(
            name=expert.name,
            cost=expert.cost_per_call,
            latency_ms=expected_latency,
            quality=base_quality,
            score=round(score, 4),
            reasons=reasons,
        )

    def plan(self, query: str, budget_latency_ms: int, budget_cost_units: int) -> RouterDecision:
        features = self._detect_features(query)
        profiles = [
            self._profile(e, features, budget_latency_ms, budget_cost_units) for e in self.experts
        ]

        mandatory = {p.name for p in profiles if features["math"] and p.name == "tool_calculator"}
        profile_lookup = {p.name: p for p in profiles}
        sorted_profiles = sorted(profiles, key=lambda p: p.score, reverse=True)

        chosen: list[str] = []
        reasons: list[str] = []
        fallback: list[str] = []
        cost_accum = 0
        latency_accum = 0

        for profile in sorted_profiles:
            would_cost = cost_accum + profile.cost
            would_latency = latency_accum + profile.latency_ms
            if would_cost > budget_cost_units or would_latency > budget_latency_ms:
                fallback.append(profile.name)
                continue
            chosen.append(profile.name)
            cost_accum = would_cost
            latency_accum = would_latency
            reasons.extend(profile.reasons)

        for required in mandatory:
            if required not in chosen:
                chosen.append(required)
                reasons.append("budget-override:math")
                required_profile = profile_lookup.get(required)
                if required_profile:
                    cost_accum += required_profile.cost
                    latency_accum += required_profile.latency_ms

        if not chosen:
            cheapest = min(sorted_profiles, key=lambda p: (p.cost, p.latency_ms))
            chosen.append(cheapest.name)
            reasons.append("fallback-cheapest")
            cost_accum = cheapest.cost
            latency_accum = cheapest.latency_ms

        return RouterDecision(
            chosen=list(dict.fromkeys(chosen)),
            reason_codes=list(dict.fromkeys(reasons)) or ["router-default"],
            estimated_latency_ms=latency_accum,
            estimated_cost_units=cost_accum,
            fallbacks=fallback,
        )


def build_router(retriever: RetrieverExpert) -> Router:
    experts: list[BaseExpert] = [ExpertSmall(), ExpertLarge(), ToolExpert(), retriever]
    return Router(experts)
