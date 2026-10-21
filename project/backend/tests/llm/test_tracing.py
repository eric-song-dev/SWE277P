import importlib

from langchain_core.tracers.context import _tracing_v2_is_enabled
from langsmith.utils import get_env_var


def test_tracing_is_forced_off_even_when_the_environment_enables_it(monkeypatch):
    import app.llm

    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.delenv("LANGSMITH_TRACING_V2", raising=False)
    get_env_var.cache_clear()
    assert _tracing_v2_is_enabled()  # the hazard is real without the switch
    importlib.reload(app.llm)  # what importing the package does in a fresh process
    assert not _tracing_v2_is_enabled()
