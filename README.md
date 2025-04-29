# spark-test-generator

A multi-agent LLM application that generates tests for Spark.

```bash
poetry install --with dev
cp .env.example .env            # add your OpenAI key
poetry run pytest -q            # everything should pass
```

You can run below commands to lint and format the files:

```bash
poetry run pre-commit run --all-files
```

Or

```bash
poetry run ruff check . --fix
poetry run ruff format .

```
