from sqlalchemy import select

from app.chat import service
from app.chat.models import ChatTurn, Conversation
from app.llm.models import LlmProfile


def test_turn_is_recorded_when_its_profile_was_deleted_meanwhile(db_session, user):
    profile = LlmProfile(
        name="Doomed", preset="custom", base_url="http://x.test/v1", model="m1", created_by=user.id
    )
    conversation = Conversation(created_by=user.id)
    db_session.add_all([profile, conversation])
    db_session.commit()
    stale_id = profile.id
    db_session.delete(profile)  # deleted after the turn loaded it, before it is recorded
    db_session.commit()

    turn_id = service._write_turn(
        conversation.id,
        user.id,
        "How many events?",
        {"outcome": "error", "error": {"code": "turn_timeout"}},
        profile_id=stale_id,
        preset="custom",
        model="m1",
        latency_ms=5,
    )

    rows = db_session.scalars(select(ChatTurn)).all()
    assert [r.id for r in rows] == [turn_id]
    assert rows[0].llm_profile_id is None
    assert (rows[0].provider, rows[0].model) == ("custom", "m1")
