from app.agents.test_generator import SharedState, after_run, next_step, END


def test_after_run_paths():
    assert after_run(SharedState(doc_url="x", test_passed=True)) == "rev"
    assert after_run(SharedState(doc_url="x", test_passed=False)) == "inc"


def test_next_step_stops_on_approval_or_limit():
    assert next_step(SharedState(doc_url="x", approved=True)) == END
    assert next_step(SharedState(doc_url="x", iterations=3)) == END
    # otherwise keep looping
    assert next_step(SharedState(doc_url="x")) == "gen"
