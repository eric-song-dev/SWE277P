"""The shape of benchmark/questions.yaml (spec 14, "Benchmark format")."""

from benchmark import load_questions
from tests.benchmark.pandas_expected import PANDAS

QUESTIONS = [
    "How many unique Biological Sciences students came to a Bagel Breakfast in Fall 2026?",
    "How many events did NetID aahmed attend in Fall 2026?",
    "Which school had the fewest unique attendees in Fall 2026?",
    "List the emails of everyone who attended any Bagel Breakfast.",
    "How many unique people attended each event type?",
    "How many unique people attended any event this term?",
    "How many people attended the Health Careers Mixer?",
    "Show the number of attendance records for each school, highest first.",
    "How many unique international students or postdocs attended at least one event?",
    (
        "Which School of Medicine students attended the October Bagel Breakfast? "
        "List their names and emails."
    ),
    "How many postdocs attended the Postdoc Wellness Lunch?",
    "Which event had the most attendees?",
    "How many unique Master's students attended a Professional Development event?",
    "List everyone who attended 5 or more events, with how many events each attended.",
    "What percentage of attendees at virtual events were doctoral students? (rounded to 1 decimal)",
    "How many attendees came to hybrid events?",
    "How many unique attendees came from each department in the School of Engineering?",
    "Who attended both Cover Letters for Academic Jobs and Teaching Statements for Academic Jobs?",
    "How many people attended exactly one event?",
    "Give me the emails of School of Social Sciences students who attended any wellness event.",
]


def test_twenty_questions_verbatim_in_order():
    questions = load_questions()
    assert [q["id"] for q in questions] == [f"q{i:02d}" for i in range(1, 21)]
    assert [q["question"] for q in questions] == QUESTIONS


def test_entry_fields():
    for q in load_questions():
        assert set(q) <= {"id", "question", "reference_sql", "ordered", "notes"}, q["id"]
        assert q["reference_sql"].strip(), q["id"]
        assert isinstance(q["ordered"], bool), q["id"]
        assert q["notes"].strip(), q["id"]  # every interpretation is written down


def test_only_q08_is_ordered():
    assert [q["id"] for q in load_questions() if q["ordered"]] == ["q08"]


def test_one_pandas_function_per_question():
    assert sorted(PANDAS) == [q["id"] for q in load_questions()]
