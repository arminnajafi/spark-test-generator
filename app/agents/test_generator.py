from __future__ import annotations

import logging
import re
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import OutputFixingParser
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.globals import set_debug
from langgraph.graph import END, StateGraph
from markdownify import MarkdownConverter

from app import ROOT_DIRECTORY, set_up_logging
from app.agents.output_parser import ExecutablePythonOutputParser
from app.config import ensure_env, settings
from app.doc_scraper import ReferencePage

# --------------------------------------------------------------------------- #
# Logging & env                                                                #
# --------------------------------------------------------------------------- #

ensure_env()
set_up_logging()
logger = logging.getLogger(__name__)
set_debug(True)

# --------------------------------------------------------------------------- #
# Prompt loader                                                                #
# --------------------------------------------------------------------------- #

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, *, must_contain: tuple[str, ...] | None = None) -> str:
    path = _PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if must_contain:
        missing = [m for m in must_contain if m not in text]
        if missing:
            raise ValueError(
                f"Prompt '{name}' missing required marker(s): {', '.join(missing)}"
            )
    return text


CODE_GENERATOR_TEMPLATE = load_prompt(
    "code_generator.txt", must_contain=("@@START_CODE@@", "@@END_CODE@@")
)
CODE_REVIEWER_TEMPLATE = load_prompt("code_reviewer.txt", must_contain=("Approved:",))


# --------------------------------------------------------------------------- #
# Utils                                                                        #
# --------------------------------------------------------------------------- #


def extract_main_content(url: str) -> str:
    logger.info("Fetching %s", url)
    resp = requests.get(url, timeout=settings.request_timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    main = soup.find("main", {"role": "main"})
    if not main:
        raise ValueError("No <main role='main'> element found in documentation page.")
    return MarkdownConverter().convert_soup(main)


@dataclass
class SharedState:
    doc_url: str
    doc_content: str | None = None
    draft_test: str | None = None
    review_notes: str | None = None
    approved: bool = False
    iterations: int = 0
    test_output: str | None = None
    test_passed: bool = False


# --------------------------------------------------------------------------- #
# LLM helpers                                                                  #
# --------------------------------------------------------------------------- #


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.model,
        max_tokens=settings.max_tokens,
        api_key=settings.openai_api_key,
        organization=settings.openai_org_id,
        timeout=settings.request_timeout,
    )


def build_code_generator_runnable():
    raw_llm = build_llm()
    fixer = OutputFixingParser.from_llm(
        parser=ExecutablePythonOutputParser(), llm=raw_llm
    )
    return raw_llm | fixer


# --------------------------------------------------------------------------- #
# Agents                                                                       #
# --------------------------------------------------------------------------- #


def code_generator(state: SharedState) -> SharedState:
    chain = build_code_generator_runnable()

    prompt = textwrap.dedent(
        f"""
        Write a pytest module for the following Spark API.
        If you see reviewer feedback, produce a **revised** code that resolves every point.

        ---------------- API reference ----------------
        {state.doc_content}
        """
    ).strip()

    if state.iterations:
        prompt += textwrap.dedent(
            f"""

            ---------------- Previous draft ----------------
            {state.draft_test}

            ---------------- Reviewer feedback -------------
            {state.review_notes}
            """
        )

    result = chain.invoke(
        [
            SystemMessage(content=CODE_GENERATOR_TEMPLATE),
            HumanMessage(content=prompt),
        ]
    )
    state.draft_test = result
    return state


def run_tests(state: SharedState) -> SharedState:
    tmp_file = tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    )
    tmp_file.write(state.draft_test or "")
    tmp_path = Path(tmp_file.name)
    tmp_file.close()

    logger.info(f"Running generated tests: python {tmp_file.name}")
    proc = subprocess.run(["pytest", str(tmp_path)], capture_output=True, text=True)
    state.test_output = proc.stdout + proc.stderr
    state.test_passed = proc.returncode == 0

    logger.info(state.test_output)

    if state.test_passed:
        logger.info("✅ Test run succeeded")
        state.review_notes = None
    else:
        logger.warning("❌ Test run failed – feeding output back to generator")
        state.review_notes = (
            "Test execution failed. Please fix the issues below and re‑emit the "
            "full file.\n\n" + textwrap.indent(state.test_output, "    ")
        )

    tmp_path.unlink(missing_ok=True)
    return state


def code_reviewer(state: SharedState) -> SharedState:
    prompt = textwrap.dedent(
        f"""
        ---------------- Draft ----------------    
        {state.draft_test}

        ---------------- API reference ----------------
        {state.doc_content}
        """
    )

    resp = (
        build_llm()
        .invoke(
            [
                SystemMessage(content=CODE_REVIEWER_TEMPLATE),
                HumanMessage(content=prompt),
            ]
        )
        .content.strip()
    )

    state.review_notes = resp
    state.approved = bool(re.search(r"Approved:\s*yes", resp, re.I))
    return state


def inc_iter(state: SharedState) -> SharedState:
    state.iterations += 1
    return state


def next_step(state: SharedState) -> str:
    return END if state.approved or state.iterations >= 3 else "gen"


def after_run(state: SharedState) -> str:
    return "rev" if state.test_passed else "inc"


def build_graph():
    g = StateGraph(SharedState)
    g.add_node("gen", code_generator)
    g.add_node("run", run_tests)
    g.add_node("rev", code_reviewer)
    g.add_node("inc", inc_iter)

    g.set_entry_point("gen")
    g.add_edge("gen", "run")
    g.add_conditional_edges("run", after_run, {"rev": "rev", "inc": "inc"})
    g.add_edge("rev", "inc")
    g.add_conditional_edges("inc", next_step, {"gen": "gen", END: END})
    return g.compile()


# --------------------------------------------------------------------------- #
# Public entry-point                                                           #
# --------------------------------------------------------------------------- #


def generate_test(reference_page: ReferencePage):
    state = SharedState(doc_url=reference_page.url)
    state.doc_content = extract_main_content(reference_page.url)

    final_state = SharedState(**build_graph().invoke(state))

    output_dir = ROOT_DIRECTORY / "output"
    output_dir.mkdir(exist_ok=True, parents=True)

    if final_state.approved:
        filename = f"test_{reference_page.title.lower().replace('.', '_')}.py"
        (output_dir / filename).write_text(
            final_state.draft_test or "", encoding="utf-8"
        )
        logger.info("✅ Review approved – wrote %s", filename)
    else:
        logger.info(
            "🚨 Not approved after %s iterations\n%s",
            final_state.iterations,
            final_state.review_notes,
        )


if __name__ == "__main__":
    _reference_page = ReferencePage(
        title="pyspark.sql.DataFrame.drop",
        url="https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.drop.html",
    )
    generate_test(_reference_page)
