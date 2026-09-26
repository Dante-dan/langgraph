"""Guard the symbols advertised by Python package `__all__` declarations."""

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

_LIBS = Path(__file__).resolve().parents[2]
_PACKAGE_ROOTS = (
    _LIBS / "langgraph" / "langgraph",
    _LIBS / "prebuilt" / "langgraph",
    _LIBS / "checkpoint" / "langgraph",
    _LIBS / "checkpoint-sqlite" / "langgraph",
    _LIBS / "checkpoint-postgres" / "langgraph",
    _LIBS / "sdk-py" / "langgraph_sdk",
)


def _declares_all(path: Path) -> bool:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in statement.targets
            ):
                return True
        elif isinstance(statement, ast.AnnAssign):
            if (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "__all__"
            ):
                return True
    return False


def _exporting_modules() -> list[str]:
    names = []
    for package_root in _PACKAGE_ROOTS:
        for path in package_root.rglob("*.py"):
            if not _declares_all(path):
                continue
            parts = path.relative_to(package_root.parent).with_suffix("").parts
            if parts[-1] == "__init__":
                parts = parts[:-1]
            names.append(".".join(parts))
    return sorted(names)


@pytest.mark.parametrize("module_name", _exporting_modules())
def test_advertised_exports_are_importable(module_name: str) -> None:
    if module_name == "langgraph_sdk.cache":
        # The optional Agent Server cache reads deployment settings at import.
        # Keep its configuration isolated from the rest of the library suite.
        env = {
            **os.environ,
            "DATABASE_URI": "postgresql://localhost/langgraph_import_test",
            "REDIS_URI": "redis://localhost:6379/15",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib; module = importlib.import_module('langgraph_sdk.cache'); "
                "[getattr(module, name) for name in module.__all__]",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        return
    module = importlib.import_module(module_name)
    for name in module.__all__:
        getattr(module, name)
