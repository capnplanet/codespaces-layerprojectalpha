from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.policy import PolicyEngine
from app.tools.registry import CalculatorTool, ToolExecutor, ToolRegistry


def _write_policy(tmpdir: Path, name: str, content: str) -> None:
    path = tmpdir / f"{name}.yaml"
    path.write_text(content, encoding="utf-8")


def test_tool_denied_by_policy():
    with TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        _write_policy(
            tmpdir,
            "deny_calc",
            """
restricted_tools:
  - tool_calculator
allowed_roles: []
denied_roles:
  - user
            """,
        )
        engine = PolicyEngine(tmpdir)
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        executor = ToolExecutor(registry, engine, max_retries=1)

        result = executor.execute(
            "tool_calculator", {"expression": "1+1"}, role="user", intents=["math"]
        )
        assert not result.success
        assert result.error == "policy_denied"


def test_tool_allowed_with_validation():
    with TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        _write_policy(tmpdir, "allow_all", "enforce_always: true\n")
        engine = PolicyEngine(tmpdir)
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        executor = ToolExecutor(registry, engine, max_retries=1)

        result = executor.execute(
            "tool_calculator",
            {"expression": "2+2"},
            role="admin",
            intents=["math"],
        )
        assert result.success
        assert result.output == "4"
