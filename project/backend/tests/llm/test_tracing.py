import importlib

import pytest
from langchain_core.callbacks import CallbackManager
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


def test_legacy_langchain_tracing_variable_does_not_break_callbacks(monkeypatch):
    """LANGCHAIN_TRACING=true makes langchain_core raise on every run unless it is forced off."""
    import app.llm

    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "LANGSMITH_TRACING_V2"):
        monkeypatch.setenv(name, "false")
    monkeypatch.setenv("LANGCHAIN_TRACING", "true")
    try:
        get_env_var.cache_clear()
        with pytest.raises(RuntimeError, match="LangChainTracerV1"):
            CallbackManager.configure()  # the hazard is real without the switch
        importlib.reload(app.llm)
        CallbackManager.configure()
    finally:
        # a failing assertion must not leave a cached "true" for later tests
        get_env_var.cache_clear()
