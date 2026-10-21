from collections.abc import Callable

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute


def _flatten(dependant: Dependant) -> set[Callable]:
    calls: set[Callable] = set()
    for sub in dependant.dependencies:
        if sub.call is not None:
            calls.add(sub.call)
        calls |= _flatten(sub)
    return calls


def routes_missing_dependency(app: FastAPI, dep: Callable) -> list[str]:
    """Return "<METHOD> <path>" for every APIRoute that does not (transitively) depend on `dep`."""
    missing: list[str] = []
    for route in app.routes:
        if isinstance(route, APIRoute) and dep not in _flatten(route.dependant):
            for method in sorted(route.methods):
                missing.append(f"{method} {route.path}")
    return missing
