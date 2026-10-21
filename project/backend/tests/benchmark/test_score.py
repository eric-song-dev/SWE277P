from decimal import Decimal

import numpy as np

from app.chat.executor import QueryResult
from benchmark.score import results_match
from tests.benchmark.pandas_expected import PANDAS


def QR(columns: list[str], rows: list[list], *, truncated: bool = False) -> QueryResult:
    return QueryResult(columns=columns, rows=rows, row_count=len(rows), truncated=truncated)


# --- from the brief ------------------------------------------------------------------------


def test_match_ignores_names_and_extra_columns():
    assert results_match(
        QR(["n"], [[6]]), QR(["unique_students", "school"], [[6, "Bio"]]), ordered=False
    )


def test_match_numeric_tolerance():
    assert results_match(QR(["p"], [[33.3]]), QR(["x"], [[Decimal("33.30")]]), ordered=False)


def test_mismatch_row_count():
    assert not results_match(QR(["e"], [["a"], ["b"]]), QR(["e"], [["a"]]), ordered=False)


def test_ordered_respected():
    assert not results_match(QR(["s"], [["a"], ["b"]]), QR(["s"], [["b"], ["a"]]), ordered=True)


def test_row_alignment_matters():
    assert not results_match(
        QR(["a", "b"], [[1, "x"], [2, "y"]]), QR(["a", "b"], [[1, "y"], [2, "x"]]), ordered=False
    )


# --- values ----------------------------------------------------------------------------------


def test_unordered_ignores_row_order():
    assert results_match(QR(["s"], [["a"], ["b"]]), QR(["s"], [["b"], ["a"]]), ordered=False)


def test_ordered_accepts_same_sequence():
    expected = QR(["s", "n"], [["a", 2], ["b", 1]])
    assert results_match(expected, QR(["n", "s"], [[2, "a"], [1, "b"]]), ordered=True)


def test_none_equals_empty_string():
    assert results_match(QR(["e"], [[None], ["a"]]), QR(["e"], [["a"], [""]]), ordered=False)


def test_number_and_numeric_string_compare_as_numbers():
    assert results_match(QR(["n"], [[6]]), QR(["n"], [["6"]]), ordered=False)
    assert results_match(QR(["p"], [[58.4]]), QR(["p"], [["58.40"]]), ordered=False)
    assert results_match(QR(["n"], [[6]]), QR(["n"], [[6.0]]), ordered=False)


def test_relative_tolerance_is_one_in_a_million():
    assert results_match(QR(["p"], [[58.4]]), QR(["p"], [[58.40000001]]), ordered=False)
    assert not results_match(QR(["p"], [[58.4]]), QR(["p"], [[58.43]]), ordered=False)
    # an unrounded value is not the rounded one the question asked for
    assert not results_match(QR(["p"], [[58.4]]), QR(["p"], [[58.42696629]]), ordered=False)


def test_whole_numbers_compare_exactly():
    # the tolerance is for fractions; counts and identifiers must be equal
    assert not results_match(QR(["n"], [[1_000_000]]), QR(["n"], [[1_000_001]]), ordered=False)
    assert not results_match(QR(["id"], [["87000000"]]), QR(["id"], [["87000050"]]), ordered=False)


def test_strings_are_exact():
    assert not results_match(QR(["s"], [["Bio"]]), QR(["s"], [["bio"]]), ordered=False)
    assert not results_match(QR(["s"], [["Bio"]]), QR(["s"], [["Bio "]]), ordered=False)


def test_text_is_not_a_number():
    assert not results_match(QR(["n"], [[6]]), QR(["n"], [["6 people"]]), ordered=False)


def test_booleans_are_not_numbers():
    assert not results_match(QR(["n"], [[1]]), QR(["n"], [[True]]), ordered=False)
    assert results_match(QR(["b"], [[True]]), QR(["b"], [[True]]), ordered=False)


def test_tolerance_inside_rows():
    expected = QR(["s", "p"], [["a", 33.3], ["b", 66.7]])
    actual = QR(["p", "s"], [[66.70000001, "b"], [Decimal("33.30"), "a"]])
    assert results_match(expected, actual, ordered=False)


def test_duplicates_count():
    assert not results_match(
        QR(["e"], [["a"], ["a"], ["b"]]), QR(["e"], [["a"], ["b"], ["b"]]), ordered=False
    )


# --- columns ---------------------------------------------------------------------------------


def test_missing_column_fails():
    expected = QR(["first", "last", "email"], [["A", "B", "a@x"]])
    assert not results_match(expected, QR(["name", "email"], [["A B", "a@x"]]), ordered=False)


def test_mapping_is_injective():
    # both expected columns hold "x"; one actual column cannot stand in for both
    assert not results_match(QR(["a", "b"], [["x", "x"]]), QR(["c"], [["x"]]), ordered=False)
    assert results_match(QR(["a", "b"], [["x", "x"]]), QR(["c", "d"], [["x", "x"]]), ordered=False)


def test_tries_other_permutations_when_columns_share_values():
    # every column holds {1, 2, 3}, so a -> x, b -> y is tried first and fails on the rows;
    # the scorer must go on to a -> y, b -> x
    expected = QR(["a", "b"], [[1, 2], [2, 3], [3, 1]])
    actual = QR(["x", "y"], [[2, 1], [3, 2], [1, 3]])
    assert results_match(expected, actual, ordered=False)
    assert results_match(expected, actual, ordered=True)
    assert not results_match(expected, QR(["x", "y"], [[1, 1], [2, 2], [3, 3]]), ordered=False)


def test_extra_column_with_same_values_does_not_hide_the_right_one():
    expected = QR(["first", "n"], [["Ann", 5], ["Bo", 6]])
    actual = QR(["last", "first", "n"], [["Bo", "Ann", 5], ["Ann", "Bo", 6]])
    assert results_match(expected, actual, ordered=False)


def test_empty_results_match():
    assert results_match(QR(["e"], []), QR(["email", "name"], []), ordered=False)
    assert not results_match(QR(["a", "b"], []), QR(["a"], []), ordered=False)


def test_truncated_result_never_matches():
    rows = [["a"], ["b"]]
    assert not results_match(QR(["e"], rows), QR(["e"], rows, truncated=True), ordered=False)


def test_numpy_numbers():
    assert results_match(QR(["p"], [[58.4]]), QR(["p"], [[np.float64(58.4)]]), ordered=False)
    assert results_match(QR(["n"], [[np.int64(6)]]), QR(["n"], [[6]]), ordered=False)
    assert not results_match(QR(["p"], [[np.float64(58.4)]]), QR(["p"], [[58.5]]), ordered=False)


# --- ties in ordered answers -------------------------------------------------------------------

RANKED = [["a", 3], ["b", 2], ["c", 2], ["d", 1]]  # b and c tie at 2


def test_ordered_tied_rows_may_swap():
    swapped = [["a", 3], ["c", 2], ["b", 2], ["d", 1]]
    assert results_match(
        QR(["s", "n"], RANKED), QR(["n", "s"], [[n, s] for s, n in swapped]), ordered=True
    )


def test_ordered_untied_rows_may_not_swap():
    for wrong in (
        [["b", 2], ["a", 3], ["c", 2], ["d", 1]],  # a (3) after b (2)
        [["a", 3], ["b", 2], ["d", 1], ["c", 2]],  # d (1) before c (2)
        [["d", 1], ["c", 2], ["b", 2], ["a", 3]],  # lowest first
    ):
        assert not results_match(QR(["s", "n"], RANKED), QR(["s", "n"], wrong), ordered=True)


def test_ordered_ties_with_duplicates():
    expected = QR(["s", "n"], [["x", 2], ["y", 2], ["y", 2], ["z", 1]])
    assert results_match(
        expected, QR(["s", "n"], [["y", 2], ["x", 2], ["y", 2], ["z", 1]]), ordered=True
    )
    # same tied counts, but the block's rows are not the expected multiset
    assert not results_match(
        expected, QR(["s", "n"], [["x", 2], ["x", 2], ["y", 2], ["z", 1]]), ordered=True
    )


def test_ordered_tie_block_does_not_span_a_gap():
    # the two 2s are not consecutive, so they are separate blocks
    expected = QR(["s", "n"], [["a", 2], ["b", 1], ["c", 2]])
    assert not results_match(expected, QR(["s", "n"], [["c", 2], ["b", 1], ["a", 2]]), ordered=True)


def test_ordered_ties_within_tolerance():
    expected = QR(["s", "p"], [["a", 33.3], ["b", 33.3], ["c", 10.5]])
    actual = QR(["s", "p"], [["b", 33.30000001], ["a", 33.3], ["c", 10.5]])
    assert results_match(expected, actual, ordered=True)


def test_ordered_without_numeric_column_is_strict():
    expected = QR(["first", "last"], [["Ann", "Lee"], ["Bo", "Lee"], ["Cy", "Ng"]])
    same = QR(["first", "last"], [["Ann", "Lee"], ["Bo", "Lee"], ["Cy", "Ng"]])
    swapped = QR(["first", "last"], [["Bo", "Lee"], ["Ann", "Lee"], ["Cy", "Ng"]])
    assert results_match(expected, same, ordered=True)
    assert not results_match(expected, swapped, ordered=True)


def test_q08_tie_between_ics_and_social_sciences():
    expected = PANDAS["q08"]()
    rows = [list(r) for r in expected.rows]
    names = [school for school, _ in rows]
    ics = names.index("School of Information and Computer Sciences")
    social = names.index("School of Social Sciences")
    assert abs(ics - social) == 1 and rows[ics][1] == rows[social][1] == 25  # the tie is real
    tie_swapped = [r[:] for r in rows]
    tie_swapped[ics], tie_swapped[social] = tie_swapped[social], tie_swapped[ics]
    assert results_match(expected, QR(["school", "records"], tie_swapped), ordered=True)
    # the top two (Engineering 55, Biological Sciences 38) are not tied
    wrong = [r[:] for r in rows]
    wrong[0], wrong[1] = wrong[1], wrong[0]
    assert not results_match(expected, QR(["school", "records"], wrong), ordered=True)
