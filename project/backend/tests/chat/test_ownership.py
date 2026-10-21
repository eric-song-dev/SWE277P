import pytest

from app.auth.models import AppUser
from app.chat.models import ChatTurn, Conversation


@pytest.fixture
def others(db_session):
    """A conversation and an answered turn that belong to a second user."""
    other = AppUser(username="other", display_name="Other Staff")
    db_session.add(other)
    db_session.flush()
    conversation = Conversation(title="Theirs", created_by=other.id)
    db_session.add(conversation)
    db_session.flush()
    turn = ChatTurn(
        conversation_id=conversation.id,
        seq=1,
        question="How many events?",
        kind="answer",
        sql="SELECT 1 AS one",
        created_by=other.id,
    )
    db_session.add(turn)
    db_session.commit()
    return conversation.id, turn.id


def test_another_users_conversation_is_not_found(client, others):
    cid, _ = others
    res = client.get(f"/api/conversations/{cid}")
    assert (res.status_code, res.json()["error"]["code"]) == (404, "conversation_not_found")
    res = client.post(f"/api/conversations/{cid}/messages", json={"question": "hi"})
    assert (res.status_code, res.json()["error"]["code"]) == (404, "conversation_not_found")


def test_another_users_turn_is_not_found(client, others):
    _, tid = others
    for path in (f"/api/chat/turns/{tid}/rerun", f"/api/chat/turns/{tid}/export"):
        res = client.get(path)
        assert (res.status_code, res.json()["error"]["code"]) == (404, "turn_not_found"), path


def test_list_shows_only_own_conversations(client, others):
    own = client.post("/api/conversations").json()["id"]
    assert [c["id"] for c in client.get("/api/conversations").json()] == [own]
    assert client.get(f"/api/conversations/{own}").status_code == 200
