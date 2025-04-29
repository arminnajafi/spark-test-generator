# Spark Test Generator using Multi-Agent LLMs

**Spark Test Generator** is a multi-agent LLM application that scrapes
Apache Spark documentation and automatically generates ready-to-run PyTest modules.

It uses an agent-based architecture to iteratively draft, refine, review, and finalize
integration tests for Spark APIs, significantly reducing manual effort and improving coverage.

---

## 🛠 Core Workflow

1. Scrape the Spark API reference page for a target function/class.
2. **Agent 1: Code Generator** drafts an initial PyTest module.
3. **Run and refine:**
    - Agent 1 automatically runs the generated tests locally.
    - If failures occur, it retries improvements until tests pass.
4. Once tests pass, the module is submitted to **Agent 2: Code Reviewer**.
5. **Review loop:**
    - If Agent 2 **approves**, the test is finalized and saved to `output/`.
    - If Agent 2 **rejects**, feedback is sent back to Agent 1 to iterate and improve.

---

## 🚀 Getting Started

```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# (Edit the .env file and add your OpenAI API key)

# Run unit tests:
poetry run pytest -q

# Start the scraping and test generation process
poetry run python main.py
```

## 🧹 Linting and Formatting

You can lint and auto-format the codebase using:

```bash
# Install with development dependencies
poetry install --with dev

# Using pre-commit
poetry run pre-commit run --all-files

# Or directly with Ruff
poetry run ruff check . --fix
poetry run ruff format .
```

---

## ⚡ License

This project is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).

---
