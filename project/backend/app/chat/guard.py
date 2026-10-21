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
_FUNCTION_CLASSES = frozenset(_CLASS_TO_NAMES)
# Functions sqlglot leaves as exp.Anonymous: allowed by name.
_ALLOWED_ANONYMOUS = frozenset({"make_date"})

# Every non-function node type that may appear in the parsed tree. Anything
# else (including any exp.Func subclass not in _CLASS_TO_NAMES) is rejected, so
# nodes this guard has never seen fail closed. Exact classes, not isinstance.
_ALLOWED_NODE_TYPES: frozenset[type[exp.Expression]] = frozenset(
    {
        # query structure
        exp.Select, exp.Union, exp.Intersect, exp.Except, exp.Subquery, exp.With, exp.CTE,
        exp.From, exp.Where, exp.Group, exp.Having, exp.Order, exp.Ordered, exp.Limit,
        exp.Offset, exp.Fetch, exp.LimitOptions, exp.Join, exp.Distinct, exp.Window,
        exp.WindowSpec, exp.Filter, exp.Table, exp.TableAlias, exp.Alias, exp.Values,
        exp.Tuple,
        # names and literals
        exp.Identifier, exp.Column, exp.Star, exp.Literal, exp.Boolean, exp.Null,
        exp.Paren, exp.Interval, exp.Var, exp.DataType, exp.DataTypeParam, exp.AtTimeZone,
        # operators and predicates
        exp.And, exp.Or, exp.Not, exp.Is, exp.In, exp.Between, exp.Like, exp.ILike,
        exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE, exp.NullSafeEQ, exp.NullSafeNEQ,
        exp.Add, exp.Sub, exp.Mul, exp.Div, exp.Mod, exp.Neg, exp.DPipe,
    }
)  # fmt: skip
_ALLOWED_NODES = _ALLOWED_NODE_TYPES | _FUNCTION_CLASSES

# CAST targets: built-in scalar types and arrays of them. Everything else
# (user-defined, schema-qualified, reg* / oid types) is rejected.
_ALLOWED_CAST_TYPES = frozenset(
    {
        exp.DType.TEXT, exp.DType.VARCHAR, exp.DType.CHAR, exp.DType.NCHAR,
        exp.DType.INT, exp.DType.BIGINT, exp.DType.SMALLINT, exp.DType.DECIMAL,
        exp.DType.DOUBLE, exp.DType.FLOAT, exp.DType.BOOLEAN,
        exp.DType.DATE, exp.DType.TIMESTAMP, exp.DType.TIMESTAMPTZ, exp.DType.TIME,
        exp.DType.TIMETZ, exp.DType.INTERVAL, exp.DType.ARRAY,
    }
)  # fmt: skip

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
    ((exp.Operator,), "custom operators (OPERATOR(...)) are not allowed"),
    ((exp.Dot,), "qualified function or type names are not allowed"),
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
    return f.sql_name().lower()


def _check_data_type(dt: exp.Expression) -> None:
    if not isinstance(dt, exp.DataType) or dt.this not in _ALLOWED_CAST_TYPES:
        raise GuardError("only built-in scalar types (and arrays of them) may be used in a cast")
    for child in dt.expressions:
        if isinstance(child, exp.DataType):
            _check_data_type(child)


def _check_nodes(root: exp.Expression) -> None:
    """Fail closed: every node must be a known function, known operator or known structure."""
    for node in root.walk():
        for types, message in _FORBIDDEN_NODES:
            if isinstance(node, types):
                raise GuardError(message)
        if isinstance(node, exp.Anonymous):
            if node.name.lower() not in _ALLOWED_ANONYMOUS:
                raise GuardError(f"function {node.name.lower()} is not allowed")
        elif type(node) not in _ALLOWED_NODES:
            if isinstance(node, exp.Func):
                raise GuardError(f"function {_function_name(node)} is not allowed")
            raise GuardError(f"the SQL construct {type(node).__name__} is not allowed")
        if isinstance(node, exp.Cast):
            _check_data_type(node.args.get("to"))
        elif isinstance(node, exp.DataType):
            _check_data_type(node)


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
    """The literal row count of an outer LIMIT / FETCH FIRST, or None if it is not a plain integer."""
    if isinstance(limit_node, exp.Limit):
        value = limit_node.expression
    elif isinstance(limit_node, exp.Fetch):
        options = limit_node.args.get("limit_options")
        if options is not None and options.args.get("with_ties"):
            raise GuardError("FETCH FIRST ... WITH TIES is not allowed; use LIMIT")
        if options is not None and options.args.get("percent"):
            raise GuardError("FETCH FIRST ... PERCENT is not allowed; use LIMIT")
        value = limit_node.args.get("count")
        if value is None:
            return 1  # FETCH FIRST ROW ONLY
    else:
        return None
    if isinstance(value, exp.Literal) and not value.is_string and value.name.isdigit():
        return int(value.name)
    return None


_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_TOKEN_REPR = re.compile(r"<Token token_type: [^,]*, text: ([^,]*),[^>]*>")


def _parse_error_reason(e: SqlglotError) -> str:
    errors = getattr(e, "errors", None)
    if errors:
        first = errors[0]
        description = _TOKEN_REPR.sub(r"'\1'", str(first.get("description", "")))
        description = _ANSI.sub("", description).strip() or "syntax error"
        where = (
            f" (line {first.get('line')}, column {first.get('col')})" if first.get("line") else ""
        )
        return f"could not parse the SQL: {description}{where}"
    return "could not parse the SQL: syntax error"


_SUBQUERY_MODIFIERS = ("limit", "offset", "order")


def _outer_query(stmt: exp.Expression) -> exp.Expression:
    """Return a query whose own LIMIT/OFFSET/ORDER are the outermost ones.

    A parenthesised top-level query is unwrapped when nothing is attached to the
    parentheses. A WITH clause is moved with it, never dropped. Any other
    modifier sqlglot attaches to the parentheses is rejected, not discarded.
    """
    while isinstance(stmt, exp.Subquery):
        extra = [
            k
            for k, v in stmt.args.items()
            if v and k not in ("this", "with_", *_SUBQUERY_MODIFIERS)
        ]
        if extra:
            raise GuardError(
                "clauses after a parenthesised query are not supported; remove the parentheses"
            )
        with_ = stmt.args.get("with_")
        inner = stmt.this
        has_mods = any(stmt.args.get(k) for k in _SUBQUERY_MODIFIERS)
        if has_mods:
            break
        if with_ is None:
            stmt = inner
            continue
        if isinstance(inner, (exp.Select, exp.SetOperation)) and not inner.args.get("with_"):
            inner.set("with_", with_.pop())
            stmt = inner
            continue
        break
    if not isinstance(stmt, exp.Subquery):
        return stmt
    # keep the parentheses as a derived table; lift WITH and the modifiers onto a wrapper
    lifted = {k: stmt.args.pop(k, None) for k in ("with_", *_SUBQUERY_MODIFIERS)}
    wrapper = exp.select("*").from_(exp.alias_(stmt, "_guarded", table=True))
    for key, value in lifted.items():
        if value is not None:
            wrapper.set(key, value)
    return wrapper


def _validate(stmt: exp.Expression | None) -> exp.Expression:
    if not isinstance(stmt, _QUERY_TYPES):
        raise GuardError("only SELECT statements are allowed")
    _check_nodes(stmt)
    _check_tables(stmt, frozenset())
    return stmt


def _parse_one(sql: str) -> exp.Expression:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except SqlglotError as e:
        raise GuardError(_parse_error_reason(e)) from None
    statements = [s for s in statements if s is not None]
    if not statements:
        raise GuardError("the SQL is empty")
    if len(statements) != 1:
        raise GuardError("exactly one statement is allowed")
    return statements[0]


def _guard(sql: str, limit: int) -> GuardedSql:
    stmt = _validate(_parse_one(strip_sql_wrapping(sql)))

    stmt = _outer_query(stmt)
    existing = _int_limit(stmt.args.get("limit"))
    final = limit if existing is None else min(existing, limit)
    stmt.set("limit", exp.Limit(expression=exp.Literal.number(final)))
    rendered = stmt.sql(dialect="postgres")
    # Safety net: whatever the rewrite did, the SQL we return must itself pass every check.
    _validate(_parse_one(rendered))
    return GuardedSql(sql=rendered, limit=final)


def guard_sql(sql: str, *, limit: int) -> GuardedSql:
    """Validate ``sql`` and cap its LIMIT. Raises GuardError for anything not accepted."""
    try:
        return _guard(sql, limit)
    except GuardError:
        raise
    except RecursionError:
        raise GuardError("the query is too deeply nested") from None
    except Exception:  # noqa: BLE001 - fail closed: never let an unexpected error escape
        raise GuardError("the SQL could not be checked; simplify the query") from None
