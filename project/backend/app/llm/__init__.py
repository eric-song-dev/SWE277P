"""LLM profiles, probing and model construction.

Privacy: this package is imported by every LLM code path (API, graph, benchmark). LangChain
would send each prompt, and with result sharing on the result rows, to LangSmith when
LANGSMITH_TRACING / LANGCHAIN_TRACING_V2 is set in a developer's shell. Row values must never
reach an external service except the profile's own model endpoint, so tracing is forced off here.
"""

import os

from langsmith.utils import get_env_var


def disable_tracing() -> None:
    # LANGCHAIN_TRACING (the legacy v1 switch) is not tracing here: langchain_core raises on
    # every run when it is set and v2 is off, so a stray "true" would fail each chat turn.
    names = (
        "LANGSMITH_TRACING",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING",
    )
    for name in names:
        os.environ[name] = "false"
    # langsmith memoizes env lookups; drop any value cached before this ran.
    get_env_var.cache_clear()


disable_tracing()
