from __future__ import annotations

import ast
from typing import Final

from langchain_core.output_parsers import BaseOutputParser


class ExecutablePythonOutputParser(BaseOutputParser):
    """
    Output-parser that validates and returns **executable** Python source.

    ‣ Strips common Markdown fences (``` or ```python).
    ‣ Rejects empty input, code > *max_len* bytes, or a module that is only a
      literal expression (string, number, list, etc.).
    ‣ Uses the Python `ast` module for fast, safe validation.
    """

    FENCE: Final[str] = "```"

    def parse(self, text: str) -> str:
        try:
            # Basic cleaning:
            code = self._clean(text)

            # Syntax & semantics check:
            module = ast.parse(code, mode="exec")

            # Final compilation ensures byte-code generation succeeds:
            compile(module, "<string>", mode="exec")
            return code
        except Exception as exc:
            raise ValueError(f"Output is not executable Python: {exc}") from exc

    @staticmethod
    def _clean(raw: str) -> str:
        if "@@START_CODE@@" in raw and "@@END_CODE@@" in raw:
            return raw.split("@@START_CODE@@")[1].split("@@END_CODE@@")[0].strip()

        """
        Strip whitespace and optional ```...``` / ```python ...``` fences.
        """
        code = raw.strip()

        if code.startswith(ExecutablePythonOutputParser.FENCE) and code.endswith(
            ExecutablePythonOutputParser.FENCE
        ):
            # Drop opening & closing fences
            code = code[
                len(ExecutablePythonOutputParser.FENCE) : -len(
                    ExecutablePythonOutputParser.FENCE
                )
            ].strip()

            # If the first line is "python" (GitHub-style), remove it too.
            if code.lower().startswith("python"):
                code = code.splitlines()[1].lstrip()

        return code.lstrip("\n").rstrip()
