import pytest

from app.auth.models import AppUser
from app.chat import service
from app.chat.models import ChatTurn, Conversation
from app.errors import HubError


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


def test_a_turn_is_never_written_into_another_users_conversation(db_session, others, user):
    cid, _ = others
    assert user.id != db_session.get(Conversation, cid).created_by
    with pytest.raises(HubError) as exc:
        service._write_turn(
            cid, user.id, "intruder", {}, profile_id=None, preset=None, model=None, latency_ms=1
        )
    assert exc.value.code == "conversation_not_found"
    assert db_session.query(ChatTurn).filter_by(conversation_id=cid).count() == 1
