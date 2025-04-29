from app.agents.test_generator import build_llm


def test_build_llm_respects_env(monkeypatch):
    """OPENAI_MODEL override should propagate into the ChatOpenAI instance."""
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    llm = build_llm()
    assert llm.model_name == "gpt-4o"
