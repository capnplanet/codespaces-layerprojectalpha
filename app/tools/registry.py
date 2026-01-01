from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.services.policy import PolicyEngine


class BaseTool:
    name: str = "base"
    description: str = ""
    input_model: type[BaseModel] = BaseModel

    def run(self, payload: BaseModel) -> str:
        raise NotImplementedError


@dataclass
class ToolExecutionResult:
    name: str
    output: str | None
    success: bool
    latency_ms: int
    error: str | None = None


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())


class ToolExecutor:
    def __init__(self, registry: ToolRegistry, policy_engine: PolicyEngine, max_retries: int = 2):
        self.registry = registry
        self.policy_engine = policy_engine
        self.max_retries = max_retries

    def _validate_and_run(self, tool: BaseTool, raw_payload: dict) -> ToolExecutionResult:
        start = time.time()
        try:
            parsed = tool.input_model.model_validate(raw_payload)
        except ValidationError as ve:
            latency_ms = int((time.time() - start) * 1000)
            return ToolExecutionResult(tool.name, None, False, latency_ms, error=str(ve))

        try:
            output = tool.run(parsed)
            latency_ms = int((time.time() - start) * 1000)
            return ToolExecutionResult(tool.name, output, True, latency_ms)
        except Exception as exc:  # pragma: no cover - guarded by retry
            latency_ms = int((time.time() - start) * 1000)
            return ToolExecutionResult(tool.name, None, False, latency_ms, error=str(exc))

    def execute(
        self, tool_name: str, payload: dict, role: str, intents: list[str]
    ) -> ToolExecutionResult:
        tool = self.registry.get(tool_name)
        if not tool:
            return ToolExecutionResult(tool_name, None, False, 0, error="tool_not_found")

        if not self.policy_engine.is_tool_allowed(role, tool_name, intents):
            return ToolExecutionResult(tool_name, None, False, 0, error="policy_denied")
        attempts = max(1, self.max_retries)
        last_result: ToolExecutionResult | None = None
        for _ in range(attempts):
            result = self._validate_and_run(tool, payload)
            last_result = result
            if result.success:
                break
        return last_result if last_result else ToolExecutionResult(tool_name, None, False, 0)


class CalculatorInput(BaseModel):
    expression: str


class CalculatorTool(BaseTool):
    name = "tool_calculator"
    description = "Evaluate safe arithmetic expressions"
    input_model = CalculatorInput

    def run(self, payload: CalculatorInput) -> str:
        expr = payload.expression.strip()
        allowed_names: dict[str, Callable] = {"abs": abs, "round": round}
        if any(
            bad in expr
            for bad in ["__", "import", "eval", "exec", "os", "sys", "open", "subprocess"]
        ):
            raise ValueError("unsafe expression")
        return str(eval(expr, {"__builtins__": allowed_names}, {}))
