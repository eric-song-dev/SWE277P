"""Each reference answer must equal an independent pandas computation over the sponsor's
compiled sheet (spec 14, A3). The reference SQL must pass the guard and run as chatbot_ro."""

import pytest

from app.chat.executor import run_readonly
from app.chat.guard import guard_sql
from benchmark import load_questions
from benchmark.score import results_match
from tests.benchmark.pandas_expected import PANDAS

pytestmark = pytest.mark.acceptance

CAP = 100_000


@pytest.mark.parametrize("q", load_questions(), ids=lambda q: q["id"])
def test_reference_sql_matches_independent_pandas(q, loaded_samples, chatbot_engine):
    actual = run_readonly(
        guard_sql(q["reference_sql"], limit=CAP).sql, max_rows=CAP, engine=chatbot_engine
    )
    expected = PANDAS[q["id"]]()
    assert not actual.truncated
    assert results_match(expected, actual, ordered=q.get("ordered", False)), (
        f"{q['id']}: pandas {expected.columns} {expected.rows[:10]} "
        f"vs SQL {actual.columns} {actual.rows[:10]}"
    )


def test_known_answers():  # pins assignment1 Appendix A values
    assert PANDAS["q01"]().rows == [[6]] and PANDAS["q02"]().rows == [[8]]
