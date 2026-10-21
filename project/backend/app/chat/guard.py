"""SQL guard (safety layer 1, spec 7.4).

Accepts a single read-only query over ``attendance_view`` that uses only
allow-listed functions. Anything unexpected is rejected (fail closed). The
read-only database role is layer 2.

``GuardError.reason`` is our own text and is safe to send back to the LLM.
"""

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

ALLOWED_TABLE = "attendance_view"

ALLOWED_FUNCTIONS: frozenset[str] = frozenset(
    {
        # aggregates
        "count", "sum", "avg", "min", "max", "string_agg", "array_agg",
        # window functions
        "row_number", "rank", "dense_rank",
        # text
        "lower", "upper", "trim", "concat", "length", "substring", "replace",
        "split_part", "position", "left", "right",
        # null handling
        "coalesce", "nullif",
        # dates
        "date_trunc", "extract", "date_part", "to_char", "make_date", "current_date",
        # numbers
        "round", "abs",
        # CAST and CASE
        "cast", "case",
    }
)  # fmt: skip

# sqlglot parses most allow-listed functions into dedicated classes instead of
# exp.Anonymous. Keys are exact classes (not isinstance): TryCast and JSONCast
# subclass Cast but are not allowed. Each value is the spec name(s) it covers.
_CLASS_TO_NAMES: dict[type[exp.Expression], frozenset[str]] = {
    exp.Count: frozenset({"count"}),
    exp.Sum: frozenset({"sum"}),
    exp.Avg: frozenset({"avg"}),
    exp.Min: frozenset({"min"}),
    exp.Max: frozenset({"max"}),
    exp.GroupConcat: frozenset({"string_agg"}),
    exp.ArrayAgg: frozenset({"array_agg"}),
    exp.RowNumber: frozenset({"row_number"}),
    exp.Rank: frozenset({"rank"}),
    exp.DenseRank: frozenset({"dense_rank"}),
    exp.Lower: frozenset({"lower"}),
    exp.Upper: frozenset({"upper"}),
    exp.Trim: frozenset({"trim"}),
    exp.Concat: frozenset({"concat"}),
    exp.Length: frozenset({"length"}),
    exp.Substring: frozenset({"substring"}),
    exp.Replace: frozenset({"replace"}),
    exp.SplitPart: frozenset({"split_part"}),
    exp.StrPosition: frozenset({"position"}),  # also strpos(); same semantics
    exp.Left: frozenset({"left"}),
    exp.Right: frozenset({"right"}),
    exp.Coalesce: frozenset({"coalesce"}),
    exp.Nullif: frozenset({"nullif"}),
    exp.TimestampTrunc: frozenset({"date_trunc"}),
    exp.Extract: frozenset({"extract", "date_part"}),  # date_part() parses to Extract
    exp.TimeToStr: frozenset({"to_char"}),
    exp.CurrentDate: frozenset({"current_date"}),
    exp.Round: frozenset({"round"}),
    exp.Abs: frozenset({"abs"}),
    exp.Cast: frozenset({"cast"}),
    exp.Case: frozenset({"case"}),
    exp.If: frozenset({"case"}),  # each WHEN branch of a CASE is an exp.If
    exp.Exists: frozenset({"exists"}),  # EXISTS (subquery): a predicate, not a function
}
_ALLOWED_CLASSES = {
    cls for cls, names in _CLASS_TO_NAMES.items() if names & (ALLOWED_FUNCTIONS | {"exists"})
}
# Functions sqlglot leaves as exp.Anonymous: allowed by name.
_ALLOWED_ANONYMOUS = frozenset({"make_date"})

_QUERY_TYPES = (exp.Select, exp.SetOperation, exp.Subquery)

_DML_MESSAGE = "data-changing statements (INSERT/UPDATE/DELETE) are not allowed"
_FORBIDDEN_NODES: tuple[tuple[tuple[type[exp.Expression], ...], str], ...] = (
    ((exp.Into,), "SELECT INTO is not allowed"),
    ((exp.Lock,), "locking clauses (FOR UPDATE/SHARE) are not allowed"),
    ((exp.DML, exp.DDL), _DML_MESSAGE),
    ((exp.Command,), "only SELECT statements are allowed"),
    (
        (
            exp.Set, exp.Transaction, exp.Commit, exp.Rollback, exp.Drop, exp.Alter,
            exp.TruncateTable, exp.Grant, exp.Revoke, exp.Execute, exp.Declare,
            exp.Pragma, exp.Attach, exp.Detach, exp.Kill, exp.Use, exp.Analyze,
            exp.Describe, exp.Show, exp.LoadData, exp.Cache, exp.Uncache, exp.Refresh,
        ),
        "only SELECT statements are allowed",
    ),
    (
        (exp.Parameter, exp.SessionParameter, exp.Placeholder),
        "query parameters and placeholders are not allowed",
    ),
)  # fmt: skip


class GuardError(Exception):
    """Raised when SQL is rejected. ``reason`` is safe to send to the LLM."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class GuardedSql:
    sql: str
    limit: int


_FENCE_START = re.compile(r"^\s*```[A-Za-z]*[ \t]*\n?")
_FENCE_END = re.compile(r"\n?\s*```\s*$")


def strip_sql_wrapping(text: str) -> str:
    """Remove Markdown code fences and trailing semicolons/whitespace."""
    text = _FENCE_START.sub("", text, count=1) if text.lstrip().startswith("```") else text
    text = _FENCE_END.sub("", text, count=1)
    return text.strip().rstrip(";").rstrip()


def _norm(ident: exp.Identifier) -> str:
    # PostgreSQL folds unquoted identifiers to lower case; quoted ones are exact.
    return ident.name if ident.args.get("quoted") else ident.name.lower()


def _function_name(f: exp.Expression) -> str:
    if isinstance(f, exp.Anonymous):
        return f.name.lower()
    return (f.sql_name() if hasattr(f, "sql_name") else type(f).__name__).lower()


def _check_functions(root: exp.Expression) -> None:
    for f in root.find_all(exp.Func):
        if isinstance(f, exp.Anonymous):
            if f.name.lower() not in _ALLOWED_ANONYMOUS:
                raise GuardError(f"function {f.name.lower()} is not allowed")
        elif type(f) not in _ALLOWED_CLASSES:
            raise GuardError(f"function {_function_name(f)} is not allowed")


def _check_nodes(root: exp.Expression) -> None:
    for node in root.walk():
        for types, message in _FORBIDDEN_NODES:
            if isinstance(node, types):
                raise GuardError(message)


_TABLE_MESSAGE = "only the attendance_view table may be queried (no schema-qualified names)"


def _check_tables(node: exp.Expression, visible: frozenset[str]) -> None:
    """Check table references with CTE scoping (a CTE is visible only after it is defined)."""
    if isinstance(node, exp.Table):
        ident = node.this
        if node.args.get("db") or node.args.get("catalog") or not isinstance(ident, exp.Identifier):
            raise GuardError(_TABLE_MESSAGE)
        name = _norm(ident)
        if name != ALLOWED_TABLE and name not in visible:
            raise GuardError(_TABLE_MESSAGE)
    scope = visible
    with_ = node.args.get("with_")
    if isinstance(with_, exp.With):
        recursive = bool(with_.args.get("recursive"))
        for cte in with_.expressions:
            alias = cte.args.get("alias")
            if not isinstance(alias, exp.TableAlias) or not isinstance(alias.this, exp.Identifier):
                raise GuardError("unsupported WITH clause")
            name = _norm(alias.this)
            _check_tables(cte.this, scope | {name} if recursive else scope)
            scope = scope | {name}
    for key, value in node.args.items():
        if key == "with_":
            continue
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, exp.Expression):
                _check_tables(child, scope)


def _int_limit(limit_node: object) -> int | None:
    if isinstance(limit_node, exp.Limit):
        value = limit_node.expression
        if isinstance(value, exp.Literal) and not value.is_string and value.name.isdigit():
            return int(value.name)
    return None


def guard_sql(sql: str, *, limit: int) -> GuardedSql:
    cleaned = strip_sql_wrapping(sql)
    try:
        statements = sqlglot.parse(cleaned, read="postgres")
    except SqlglotError as e:
        raise GuardError(f"could not parse the SQL: {e}") from None
    statements = [s for s in statements if s is not None]
    if not statements:
        raise GuardError("the SQL is empty")
    if len(statements) != 1:
        raise GuardError("exactly one statement is allowed")
    stmt = statements[0]
    if not isinstance(stmt, _QUERY_TYPES):
        raise GuardError("only SELECT statements are allowed")

    _check_nodes(stmt)
    _check_functions(stmt)
    _check_tables(stmt, frozenset())

    if isinstance(stmt, exp.Subquery):
        stmt = exp.select("*").from_(stmt)
    existing = _int_limit(stmt.args.get("limit"))
    final = limit if existing is None else min(existing, limit)
    stmt.set("limit", exp.Limit(expression=exp.Literal.number(final)))
    return GuardedSql(sql=stmt.sql(dialect="postgres"), limit=final)
