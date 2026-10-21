from collections.abc import Callable, Iterator

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import iter_route_contexts


def _flatten(dependant: Dependant) -> set[Callable]:
    calls: set[Callable] = set()
    for sub in dependant.dependencies:
        if sub.call is not None:
            calls.add(sub.call)
        calls |= _flatten(sub)
    return calls


def api_routes(app: FastAPI) -> Iterator[tuple[str, str, Dependant]]:
    """Yield (method, path, dependant) for every API route, including those on included routers.

    `app.routes` only holds a wrapper per included router in this FastAPI version, so walk the
    effective route contexts instead.
    """
    for ctx in iter_route_contexts(app.routes):
        dependant = getattr(ctx, "dependant", None)
        if dependant is None:  # docs and openapi routes
            continue
        for method in sorted(ctx.methods or ()):
            yield method, ctx.path, dependant


def routes_missing_dependency(app: FastAPI, dep: Callable) -> list[str]:
    """Return "<METHOD> <path>" for every API route that does not (transitively) depend on `dep`."""
    return [
        f"{method} {path}"
        for method, path, dependant in api_routes(app)
        if dep not in _flatten(dependant)
    ]
