import re

import pytest
import sqlglot

from app.chat import guard
from app.chat.guard import ALLOWED_FUNCTIONS, GuardError, guard_sql, strip_sql_wrapping

OK = [
    "SELECT COUNT(DISTINCT person_key) FROM attendance_view WHERE school = 'School of Biological Sciences'",
    "WITH b AS (SELECT * FROM attendance_view WHERE event_name ILIKE 'Bagel%') SELECT email FROM b",
    "SELECT school, count(*) FROM attendance_view GROUP BY school ORDER BY 2 DESC",
    (
        "SELECT lower(email), coalesce(school, 'Unknown'), CAST(event_date AS text), "
        "CASE WHEN netid IS NULL THEN 1 ELSE 0 END FROM attendance_view"
    ),
    (
        "SELECT round(100.0 * count(*) FILTER (WHERE affiliation = 'Doctoral Student') / count(*), 1) "
        "FROM attendance_view"
    ),
    "SELECT event_name, rank() OVER (ORDER BY count(*) DESC) FROM attendance_view GROUP BY event_name",
    (
        "SELECT string_agg(email, ', '), date_trunc('month', event_date), extract(year FROM event_date), "
        "to_char(event_date, 'YYYY'), current_date FROM attendance_view GROUP BY 2, 3, 4"
    ),
    # no FROM at all
    "SELECT current_date",
    # set operations, parenthesised branches, subqueries, EXISTS
    "SELECT email FROM attendance_view UNION SELECT netid FROM attendance_view",
    "(SELECT email FROM attendance_view) INTERSECT (SELECT email FROM attendance_view)",
    "SELECT email FROM attendance_view EXCEPT SELECT netid FROM attendance_view",
    "SELECT email FROM attendance_view a WHERE a.person_key IN (SELECT person_key FROM attendance_view)",
    "SELECT email FROM attendance_view a WHERE EXISTS (SELECT 1 FROM attendance_view b WHERE b.netid = a.netid)",
    "SELECT a.email FROM attendance_view a JOIN attendance_view b ON a.netid = b.netid",
    "SELECT email::text FROM attendance_view",
    # a CTE chain and a CTE referencing an earlier CTE
    "WITH a AS (SELECT * FROM attendance_view), b AS (SELECT * FROM a) SELECT * FROM b",
    "WITH RECURSIVE r AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM r WHERE n < 5) SELECT n FROM r",
    # quoted but exactly the right name
    'SELECT "email" FROM "attendance_view"',
    "SELECT * FROM ATTENDANCE_VIEW",
    # CTE named like a real table is fine when it only reads attendance_view
    "WITH app_user AS (SELECT * FROM attendance_view) SELECT * FROM app_user",
]

# label -> SQL expression exercising an allow-listed function
FUNCTION_CASES = {
    "count": "count(*)",
    "sum": "sum(person_key)",
    "avg": "avg(person_key)",
    "min": "min(event_date)",
    "max": "max(event_date)",
    "string_agg": "string_agg(email, ',')",
    "array_agg": "array_agg(email)",
    "row_number": "row_number() OVER (ORDER BY event_date)",
    "rank": "rank() OVER (ORDER BY event_date)",
    "dense_rank": "dense_rank() OVER (ORDER BY event_date)",
    "lower": "lower(email)",
    "upper": "upper(email)",
    "trim": "trim(email)",
    "concat": "concat(first_name, ' ', last_name)",
    "length": "length(email)",
    "substring": "substring(email, 1, 3)",
    "substring_from": "substring(email FROM 1 FOR 3)",
    "replace": "replace(email, 'a', 'b')",
    "split_part": "split_part(email, '@', 2)",
    "position": "position('@' IN email)",
    "left": "left(email, 2)",
    "right": "right(email, 2)",
    "coalesce": "coalesce(school, 'x')",
    "nullif": "nullif(school, '')",
    "date_trunc": "date_trunc('month', event_date)",
    "extract": "extract(year FROM event_date)",
    "date_part": "date_part('year', event_date)",
    "to_char": "to_char(event_date, 'YYYY')",
    "make_date": "make_date(2025, 1, 2)",
    "current_date": "current_date",
    "round": "round(person_key)",
    "round2": "round(person_key, 2)",
    "abs": "abs(person_key)",
    "cast": "cast(person_key AS text)",
    "double_colon": "person_key::text",
    "case": "CASE WHEN school IS NULL THEN 'a' WHEN school = 'b' THEN 'c' ELSE 'd' END",
}


def test_every_allowed_function_has_a_case():
    exprs = " ".join(FUNCTION_CASES.values()).lower()
    for name in ALLOWED_FUNCTIONS:
        pattern = {"case": "case when", "cast": "cast("}.get(name, name.replace("_", "_") + "(")
        assert pattern in exprs or name == "current_date", name


@pytest.mark.parametrize("expr", FUNCTION_CASES.values())
def test_each_allowed_function(expr):
    guard_sql(f"SELECT {expr} FROM attendance_view", limit=1001)


@pytest.mark.parametrize("sql", OK)
def test_allowed(sql):
    guard_sql(sql, limit=1001)


BAD = {
    "DROP TABLE hub.attendance": "SELECT",
    "DELETE FROM attendance_view": "SELECT",
    "SELECT 1; DELETE FROM attendance_view": "one statement",
    "SELECT * FROM hub.app_user": "attendance_view",
    "SELECT * FROM app_user": "attendance_view",
    "SELECT pg_sleep(10)": "pg_sleep",
    "SELECT set_config('statement_timeout', '0', false)": "set_config",
    "SELECT * FROM pg_catalog.pg_roles": "attendance_view",
    "SELECT * INTO t FROM attendance_view": "INTO",
    "SELECT * FROM attendance_view FOR UPDATE": "lock",
    "SELECT current_setting('role')": "current_setting",
    "SELECT * FROM information_schema.tables": "attendance_view",
    # empty / unparsable
    "": "empty",
    "-- nothing here": "empty",
    "SELECT FROM WHERE (": "could not parse",
    # more than one statement, including ones hidden by comments
    "SELECT 1 FROM attendance_view /* x */; DROP TABLE hub.app_user": "one statement",
    "SELECT 1 FROM attendance_view; -- x\nSELECT 2 FROM attendance_view": "one statement",
    # not a SELECT
    "COPY attendance_view TO '/tmp/x'": "SELECT",
    "SET role chatbot_ro": "SELECT",
    "RESET ALL": "SELECT",
    "EXPLAIN ANALYZE SELECT 1 FROM attendance_view": "SELECT",
    "EXPLAIN SELECT 1 FROM attendance_view": "SELECT",
    "CALL do_it()": "SELECT",
    "DO $$ BEGIN PERFORM pg_sleep(1); END $$": "SELECT",
    "VACUUM": "SELECT",
    "LISTEN chan": "SELECT",
    "NOTIFY chan": "SELECT",
    "BEGIN": "SELECT",
    "SHOW ALL": "SELECT",
    "TRUNCATE hub.attendance": "SELECT",
    "INSERT INTO attendance_view VALUES (1)": "SELECT",
    "UPDATE attendance_view SET email = 'x'": "SELECT",
    "GRANT ALL ON attendance_view TO public": "SELECT",
    "VALUES (1)": "SELECT",
    "TABLE attendance_view": "SELECT",
    # data-changing statements inside CTEs
    "WITH x AS (DELETE FROM hub.attendance RETURNING *) SELECT * FROM x": "INSERT/UPDATE/DELETE",
    "WITH x AS (INSERT INTO t VALUES (1) RETURNING *) SELECT * FROM x": "INSERT/UPDATE/DELETE",
    "WITH x AS (UPDATE t SET a = 1 RETURNING *) SELECT * FROM x": "INSERT/UPDATE/DELETE",
    # forbidden functions in every position
    "SELECT lower(pg_sleep(1)) FROM attendance_view": "pg_sleep",
    "SELECT coalesce(current_setting('x'), 'y') FROM attendance_view": "current_setting",
    "SELECT email FROM attendance_view WHERE pg_sleep(1) IS NOT NULL": "pg_sleep",
    "SELECT email FROM attendance_view ORDER BY pg_sleep(1)": "pg_sleep",
    "SELECT email FROM attendance_view GROUP BY email HAVING pg_sleep(1) IS NULL": "pg_sleep",
    "WITH a AS (SELECT pg_sleep(1) AS s FROM attendance_view) SELECT * FROM a": "pg_sleep",
    "SELECT * FROM (SELECT dblink('x', 'y') FROM attendance_view) s": "dblink",
    "SELECT lo_import('/etc/passwd')": "lo_import",
    "SELECT pg_read_file('/etc/passwd')": "pg_read_file",
    "SELECT email FROM attendance_view WHERE person_key IN (SELECT nextval('s'))": "nextval",
    "SELECT CASE WHEN true THEN pg_sleep(1) END": "pg_sleep",
    "SELECT CAST(pg_sleep(1) AS text)": "pg_sleep",
    "SELECT sum(x) OVER (ORDER BY pg_sleep(1)) FROM attendance_view": "pg_sleep",
    "SELECT count(*) FILTER (WHERE pg_sleep(1) IS NULL) FROM attendance_view": "pg_sleep",
    "SELECT email FROM attendance_view a JOIN attendance_view b ON pg_sleep(1) IS NULL": "pg_sleep",
    # allowed-looking but not on the list
    "SELECT now()": "not allowed",
    "SELECT current_timestamp": "not allowed",
    "SELECT current_user": "not allowed",
    "SELECT version()": "not allowed",
    "SELECT greatest(1, 2)": "not allowed",
    "SELECT TRY_CAST('1' AS int)": "not allowed",
    "SELECT email ~ 'a' FROM attendance_view": "not allowed",
    "SELECT unnest(ARRAY[1,2])": "not allowed",
    "SELECT ARRAY[1,2]": "not allowed",
    "SELECT email -> 'a' FROM attendance_view": "not allowed",
    # forbidden tables in every position
    "WITH a AS (SELECT * FROM hub.app_user) SELECT * FROM a": "attendance_view",
    "WITH a AS (SELECT * FROM app_user) SELECT * FROM a": "attendance_view",
    "SELECT * FROM attendance_view WHERE person_key IN (SELECT id FROM app_user)": "attendance_view",
    "SELECT * FROM (SELECT * FROM pg_roles) s": "attendance_view",
    "SELECT email FROM attendance_view UNION SELECT rolname FROM pg_roles": "attendance_view",
    "SELECT rolname FROM pg_roles UNION SELECT email FROM attendance_view": "attendance_view",
    "SELECT email FROM attendance_view EXCEPT (SELECT rolname FROM pg_roles)": "attendance_view",
    "SELECT email FROM attendance_view, pg_roles": "attendance_view",
    "SELECT email FROM attendance_view JOIN pg_roles ON true": "attendance_view",
    "SELECT email FROM attendance_view CROSS JOIN LATERAL (SELECT * FROM pg_roles) r": "Lateral",
    "SELECT * FROM public.attendance_view": "attendance_view",
    "SELECT * FROM hub.attendance_view": "attendance_view",
    "SELECT * FROM mydb.hub.attendance_view": "attendance_view",
    'SELECT * FROM "pg_catalog"."pg_roles"': "attendance_view",
    'SELECT * FROM "ATTENDANCE_VIEW"': "attendance_view",
    'SELECT * FROM "hub"."attendance_view"': "attendance_view",
    # CTE shadowing: the CTE's own body reads the real table
    "WITH app_user AS (SELECT * FROM app_user) SELECT * FROM app_user": "attendance_view",
    "WITH pg_roles AS (SELECT * FROM pg_roles) SELECT * FROM pg_roles": "attendance_view",
    "WITH app_user AS (SELECT 1) SELECT * FROM hub.app_user": "attendance_view",
    "WITH a AS (SELECT 1) SELECT * FROM (WITH b AS (SELECT 1) SELECT 1) s, b": "attendance_view",
    "SELECT * FROM (WITH c AS (SELECT 1) SELECT * FROM c) s, c": "attendance_view",
    "WITH a AS (SELECT * FROM b), b AS (SELECT 1) SELECT * FROM a": "attendance_view",
    # table-valued functions in FROM
    "SELECT * FROM generate_series(1, 10)": "not allowed",
    "SELECT * FROM pg_ls_dir('/')": "pg_ls_dir",
    "SELECT * FROM attendance_view, generate_series(1, 10)": "not allowed",
    "SELECT * FROM unnest(ARRAY[1])": "not allowed",
    "SELECT * FROM ROWS FROM (pg_ls_dir('/'))": "not allowed",
    # parameters/placeholders
    "SELECT * FROM attendance_view WHERE email = :x": "parameter",
    "SELECT * FROM attendance_view WHERE email = $1": "parameter",
    # locking variants
    "SELECT * FROM attendance_view FOR SHARE": "lock",
    "SELECT * FROM attendance_view FOR UPDATE NOWAIT": "lock",
    "SELECT * FROM (SELECT * FROM attendance_view FOR UPDATE) s": "lock",
    "SELECT * INTO TEMP t FROM attendance_view": "INTO",
}


@pytest.mark.parametrize(("sql", "needle"), BAD.items())
def test_rejected(sql, needle):
    with pytest.raises(GuardError, match=re.compile(needle, re.IGNORECASE)):
        guard_sql(sql, limit=1001)


def test_parse_error_reason_is_guard_error():
    with pytest.raises(GuardError) as e:
        guard_sql("SELECT FROM WHERE (", limit=10)
    assert isinstance(e.value.reason, str)
    assert str(e.value) == e.value.reason


def test_limit_added():
    assert guard_sql("SELECT email FROM attendance_view", limit=1001).sql.endswith("LIMIT 1001")


def test_limit_tightened():
    assert (
        "LIMIT 1001" in guard_sql("SELECT email FROM attendance_view LIMIT 50000", limit=1001).sql
    )


def test_smaller_limit_kept():
    assert "LIMIT 5" in guard_sql("SELECT email FROM attendance_view LIMIT 5", limit=1001).sql


def test_result_reports_limit():
    assert guard_sql("SELECT email FROM attendance_view LIMIT 5", limit=1001).limit == 5
    assert guard_sql("SELECT email FROM attendance_view", limit=1001).limit == 1001


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT email FROM attendance_view LIMIT ALL",
        "SELECT email FROM attendance_view LIMIT (SELECT 5)",
        "SELECT email FROM attendance_view LIMIT 5 + 5000",
        "SELECT email FROM attendance_view FETCH FIRST 50000 ROWS ONLY",
    ],
)
def test_non_literal_limit_replaced(sql):
    out = guard_sql(sql, limit=1001).sql
    assert out.endswith("LIMIT 1001")
    assert out.count("LIMIT") == 1
    assert "ALL" not in out
    assert "SELECT 5" not in out


def test_only_outer_limit_changes():
    out = guard_sql(
        "SELECT * FROM (SELECT email FROM attendance_view LIMIT 99999) s LIMIT 99999", limit=1001
    ).sql
    assert "LIMIT 99999" in out
    assert out.endswith("LIMIT 1001")


def test_offset_kept():
    out = guard_sql("SELECT email FROM attendance_view LIMIT 50000 OFFSET 20", limit=1001).sql
    assert "LIMIT 1001" in out
    assert "OFFSET 20" in out


def test_set_operation_limit_applies_to_whole_query():
    out = guard_sql(
        "SELECT email FROM attendance_view UNION SELECT netid FROM attendance_view", limit=1001
    ).sql
    assert out.endswith("LIMIT 1001")
    out = guard_sql(
        "SELECT email FROM attendance_view UNION SELECT netid FROM attendance_view LIMIT 7",
        limit=1001,
    ).sql
    assert out.endswith("LIMIT 7")


def test_parenthesised_query_limited():
    out = guard_sql("(SELECT email FROM attendance_view)", limit=1001).sql
    assert "LIMIT 1001" in out


def test_fences_and_semicolon_in_guard():
    out = guard_sql("```sql\nSELECT email FROM attendance_view;\n```", limit=3).sql
    assert out == "SELECT email FROM attendance_view LIMIT 3"


def test_output_is_postgres_sql():
    out = guard_sql("SELECT email::text FROM attendance_view", limit=3).sql
    assert "::TEXT" in out.upper() or "CAST" in out.upper()


def test_strips_fences_and_semicolon():
    assert (
        strip_sql_wrapping("```sql\nSELECT 1 FROM attendance_view;\n```")
        == "SELECT 1 FROM attendance_view"
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SELECT 1;", "SELECT 1"),
        ("  SELECT 1 ;; \n", "SELECT 1"),
        ("```\nSELECT 1\n```", "SELECT 1"),
        ("```SQL\nSELECT 1;\n```  ", "SELECT 1"),
        ("SELECT 1", "SELECT 1"),
    ],
)
def test_strip_variants(raw, expected):
    assert strip_sql_wrapping(raw) == expected


# ---- fix round 1 -----------------------------------------------------------

ORDINARY_OK = [
    (
        "SELECT DISTINCT email FROM attendance_view WHERE event_name ILIKE 'Bagel Breakfast%' "
        "AND email IS NOT NULL ORDER BY email"
    ),
    (
        "SELECT COUNT(DISTINCT person_key) AS n FROM attendance_view "
        "WHERE school = 'School of Biological Sciences' AND event_name ILIKE 'Bagel Breakfast%'"
    ),
    "SELECT email FROM attendance_view WHERE school = 'a' OR school = 'b'",
    "SELECT email FROM attendance_view WHERE (school = 'a' OR school = 'b') AND NOT netid IS NULL",
    "SELECT a.email FROM attendance_view a JOIN attendance_view b ON a.netid = b.netid AND a.school = b.school",
    "SELECT count(*) FILTER (WHERE school = 'a' AND event_type = 'b') FROM attendance_view",
    "SELECT CASE WHEN school = 'a' AND netid IS NOT NULL OR email LIKE '%x' THEN 1 ELSE 0 END FROM attendance_view",
    "SELECT school FROM attendance_view GROUP BY school HAVING count(*) > 1 AND count(*) <= 10 OR sum(person_key) <> 3",
    (
        "SELECT email FROM attendance_view WHERE person_key IN (1, 2) AND person_key NOT IN (3) "
        "AND person_key BETWEEN 1 AND 5 AND email NOT ILIKE 'x%' AND school != 'x' AND school IS DISTINCT FROM 'y'"
    ),
    (
        "SELECT email, (person_key + 1) * 2 - 3 / 4 % 5 AS v, -person_key, email || '!' FROM attendance_view "
        "WHERE person_key >= 1 AND person_key < 9 AND person_key > 0 ORDER BY v DESC NULLS LAST, 1 OFFSET 3"
    ),
    "SELECT event_date AT TIME ZONE 'UTC', interval '1 day', DATE '2020-01-01' FROM attendance_view",
    (
        "SELECT x::numeric(10,2), x::double precision, x::timestamptz, x::text[], x::varchar(5), x::int, "
        "x::bigint, x::boolean, x::date, x::interval FROM (SELECT 1 AS x) s"
    ),
    "SELECT * FROM (VALUES (1, 'a')) AS v(n, s)",
    "SELECT DISTINCT ON (school) school, email FROM attendance_view",
    (
        "SELECT count(*) OVER (PARTITION BY school ORDER BY event_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) "
        "FROM attendance_view"
    ),
    "SELECT a.email FROM attendance_view a LEFT JOIN attendance_view b USING (netid) CROSS JOIN attendance_view c",
]


@pytest.mark.parametrize("sql", ORDINARY_OK)
def test_ordinary_queries_pass(sql):
    guard_sql(sql, limit=1001)


@pytest.mark.parametrize(
    "sql",
    [*OK, *ORDINARY_OK, *[f"SELECT {e} FROM attendance_view" for e in FUNCTION_CASES.values()]],
)
def test_every_node_type_in_ok_queries_is_allowed(sql):
    tree = sqlglot.parse_one(sql, read="postgres")
    for node in tree.walk():
        if isinstance(node, sqlglot.exp.Anonymous):
            continue
        assert type(node) in guard._ALLOWED_NODES, type(node).__name__


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT email FROM attendance_view TABLESAMPLE SYSTEM (10)",
        "SELECT school FROM attendance_view GROUP BY ROLLUP (school)",
        "SELECT (ARRAY[1])[1]",
        "SELECT email FROM attendance_view WHERE email = ANY (ARRAY['a'])",
        "SELECT x FROM attendance_view, UNNEST(ARRAY[1]) AS x",
    ],
)
def test_unknown_node_types_fail_closed(sql):
    with pytest.raises(GuardError, match="not allowed"):
        guard_sql(sql, limit=10)


def test_unlisted_node_type_is_rejected(monkeypatch):
    # an otherwise fine query fails once a node type it uses is not on the allow-list
    monkeypatch.setattr(guard, "_ALLOWED_NODES", guard._ALLOWED_NODES - {sqlglot.exp.Like})
    with pytest.raises(GuardError, match="Like is not allowed"):
        guard_sql("SELECT email FROM attendance_view WHERE email LIKE 'a%'", limit=10)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT NULL::hub.app_user",
        "SELECT CAST('x' AS pg_catalog.regclass)",
        "SELECT 'pg_shadow'::regclass::text",
        "SELECT 10::regrole",
        "SELECT 'pg_sleep'::regproc",
        "SELECT regclass 'pg_roles'",
        "SELECT 'x'::oid",
        "SELECT 'x'::name",
        "SELECT 'x'::json",
        "SELECT 'x'::citext",
        "SELECT TRY_CAST('1' AS int)",
        "SELECT 'x' OPERATOR(pg_catalog.~) 'y'",
        "SELECT 1 OPERATOR(hub.===) 1",
        "SELECT hub.make_date(2025, 1, 1)",
        "SELECT pg_catalog.make_date(2025, 1, 1)",
        "SELECT pg_catalog.lower('x')",
    ],
)
def test_qualified_names_and_catalog_lookups_rejected(sql):
    with pytest.raises(GuardError):
        guard_sql(sql, limit=10)


# LIMIT / FETCH / parenthesised queries

LIMIT_CASES = [
    (
        "SELECT email FROM attendance_view FETCH FIRST 5 ROWS ONLY",
        "SELECT email FROM attendance_view LIMIT 5",
        5,
    ),
    (
        "SELECT email FROM attendance_view FETCH FIRST 50000 ROWS ONLY",
        "SELECT email FROM attendance_view LIMIT 1001",
        1001,
    ),
    (
        "SELECT email FROM attendance_view FETCH FIRST ROW ONLY",
        "SELECT email FROM attendance_view LIMIT 1",
        1,
    ),
    ("(SELECT email FROM attendance_view) LIMIT 5", None, 5),
    ("(SELECT email FROM attendance_view) LIMIT 50000", None, 1001),
    ("(SELECT email FROM attendance_view) FETCH FIRST 3 ROWS ONLY", None, 3),
    ("(SELECT email FROM attendance_view) ORDER BY email LIMIT 7 OFFSET 2", None, 7),
    ("((SELECT email FROM attendance_view))", "SELECT email FROM attendance_view LIMIT 1001", 1001),
    ("(SELECT email FROM attendance_view LIMIT 3)", "SELECT email FROM attendance_view LIMIT 3", 3),
]


@pytest.mark.parametrize(("sql", "expected", "n"), LIMIT_CASES)
def test_fetch_and_parenthesised_limits(sql, expected, n):
    out = guard_sql(sql, limit=1001)
    assert out.limit == n
    assert out.sql.count("LIMIT") == 1
    assert "FETCH" not in out.sql
    assert out.sql.endswith(f"LIMIT {n}") or "OFFSET" in out.sql
    if expected is not None:
        assert out.sql == expected
    # the rendered SQL must itself be valid and pass the guard unchanged
    assert guard_sql(out.sql, limit=1001).sql == out.sql


def test_wrapped_query_keeps_order_and_offset():
    out = guard_sql(
        "(SELECT email FROM attendance_view) ORDER BY email LIMIT 7 OFFSET 2", limit=1001
    ).sql
    assert "ORDER BY email" in out
    assert "LIMIT 7" in out
    assert "OFFSET 2" in out


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT email FROM attendance_view FETCH FIRST 5 ROWS WITH TIES",
        "SELECT email FROM attendance_view FETCH FIRST 5 PERCENT ROWS ONLY",
    ],
)
def test_fetch_with_ties_and_percent_rejected(sql):
    with pytest.raises(GuardError, match="FETCH"):
        guard_sql(sql, limit=10)


# robustness


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT " + "(" * 60 + "1" + ")" * 60,
        "SELECT * FROM " + "(SELECT * FROM " * 250 + "attendance_view" + ")" * 250,
        "SELECT " + "+".join(["1"] * 3000),
    ],
)
def test_deep_nesting_is_a_guard_error(sql):
    with pytest.raises(GuardError):
        guard_sql(sql, limit=10)


def test_unexpected_exception_becomes_guard_error(monkeypatch):
    def boom(*a, **k):
        raise ValueError("secret internal detail")

    monkeypatch.setattr(guard, "_check_tables", boom)
    with pytest.raises(GuardError) as e:
        guard_sql("SELECT email FROM attendance_view", limit=10)
    assert "secret" not in e.value.reason


@pytest.mark.parametrize(
    "sql", ["SELECT FROM WHERE (", "SELECT 1 +", "SELECT a b c d FROM attendance_view"]
)
def test_parse_error_reason_is_clean(sql):
    with pytest.raises(GuardError) as e:
        guard_sql(sql, limit=10)
    reason = e.value.reason
    assert reason.startswith("could not parse the SQL")
    assert "\x1b" not in reason
    assert "<Token" not in reason
    assert "token_type" not in reason
    assert "line 1" in reason


# ---- fix round 2 -----------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "WITH pg_roles AS (SELECT 1 AS x) (SELECT * FROM pg_roles) WHERE true",
        "WITH pg_settings AS (SELECT 1 AS x) (SELECT name, setting FROM pg_settings) GROUP BY 1",
        "WITH pg_stat_activity AS (SELECT 1 AS x) (SELECT query FROM pg_stat_activity) WINDOW w AS ()",
        "WITH pg_class AS (SELECT 1 AS x) (SELECT relname FROM pg_class) HAVING true",
    ],
)
def test_trailing_clauses_after_parentheses_rejected(sql):
    with pytest.raises(GuardError, match="parenthesised"):
        guard_sql(sql, limit=1001)


def test_with_kept_when_unwrapping():
    out = guard_sql("WITH a AS (SELECT email FROM attendance_view) (SELECT * FROM a)", limit=1001)
    assert out.sql == "WITH a AS (SELECT email FROM attendance_view) SELECT * FROM a LIMIT 1001"


@pytest.mark.parametrize(
    ("sql", "n"),
    [
        ("WITH a AS (SELECT email FROM attendance_view) (SELECT * FROM a) LIMIT 5", 5),
        ("WITH a AS (SELECT email FROM attendance_view) (SELECT * FROM a) LIMIT 50000", 1001),
        (
            "WITH a AS (SELECT email FROM attendance_view) (SELECT * FROM a) FETCH FIRST 3 ROWS ONLY",
            3,
        ),
        (
            "WITH a AS (SELECT email FROM attendance_view) (SELECT * FROM a) ORDER BY email LIMIT 4 OFFSET 1",
            4,
        ),
    ],
)
def test_with_plus_parenthesised_query_with_modifiers(sql, n):
    out = guard_sql(sql, limit=1001)
    assert out.limit == n
    assert out.sql.startswith("WITH a AS (SELECT email FROM attendance_view) SELECT * FROM (")
    assert out.sql.count("LIMIT") == 1
    assert guard_sql(out.sql, limit=1001).sql == out.sql


def test_rendered_sql_is_revalidated(monkeypatch):
    def evil(stmt):
        return sqlglot.parse_one("SELECT * FROM pg_roles", read="postgres")

    monkeypatch.setattr(guard, "_outer_query", evil)
    with pytest.raises(GuardError, match="attendance_view"):
        guard_sql("SELECT email FROM attendance_view", limit=10)
