import re

import pytest

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
    "SELECT email FROM attendance_view CROSS JOIN LATERAL (SELECT * FROM pg_roles) r": "attendance_view",
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
