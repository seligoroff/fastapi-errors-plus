"""Guard tests for README fenced Python blocks."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


_PYTHON_FENCE_RE = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)


def _extract_python_blocks(text: str) -> list[str]:
    return [match.group(1) for match in _PYTHON_FENCE_RE.finditer(text)]


@pytest.mark.unit
@pytest.mark.parametrize("readme_path", ["README.md", "README.ru.md"])
def test_readme_python_fences_are_ast_valid(readme_path: str) -> None:
    text = Path(readme_path).read_text(encoding="utf-8")
    blocks = _extract_python_blocks(text)
    assert blocks, f"No python code fences found in {readme_path}"

    syntax_errors: list[str] = []
    for idx, block in enumerate(blocks, start=1):
        try:
            ast.parse(block)
        except SyntaxError as exc:
            syntax_errors.append(
                f"{readme_path}: block #{idx}, line {exc.lineno}, offset {exc.offset}: {exc.msg}"
            )

    assert not syntax_errors, "README python fence syntax errors:\n" + "\n".join(syntax_errors)
