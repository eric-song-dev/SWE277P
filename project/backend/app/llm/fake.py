import asyncio
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Self

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import BaseModel, Field

from app.chat.graph import prompts

SCRIPT_PATH = Path(__file__).with_name("fake_script.json")
UNMATCHED_REPLY = json.dumps(
    {
        "kind": "clarify",
        "clarification_question": "The demo model only knows its scripted questions.",
    }
)
UNMATCHED_ANALYSIS = "The demo model has no scripted analysis for this question."


class ScriptEntry(BaseModel):
    match: str  # case-insensitive substring of the question
    generate: list[str]  # raw replies, used in order; the last one repeats
    analyze: str
    delay_seconds: float = 0  # pause before a generate reply (analyze is never delayed)


class ScriptedChatModel(BaseChatModel):
    """Offline model for tests, Playwright and demos: replies are keyed by the question."""

    script: list[ScriptEntry]
    calls: list[list[BaseMessage]] = Field(default_factory=list)
    used: dict[int, int] = Field(default_factory=dict)

    @classmethod
    def default(cls) -> Self:
        raw = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
        return cls(script=[ScriptEntry.model_validate(e) for e in raw])

    @property
    def _llm_type(self) -> str:
        return "scripted-fake"

    def _reply(self, messages: Sequence[BaseMessage]) -> str:
        self.calls.append(list(messages))
        question = next(
            (str(m.content) for m in reversed(messages) if isinstance(m, HumanMessage)), ""
        ).lower()
        is_analyze = any(
            m.type == "system" and m.content == prompts.ANALYZE_SYSTEM for m in messages
        )
        for i, entry in enumerate(self.script):
            if entry.match.lower() in question:
                if is_analyze:
                    return entry.analyze
                n = self.used.get(i, 0)
                self.used[i] = n + 1
                return entry.generate[min(n, len(entry.generate) - 1)]
        return UNMATCHED_ANALYSIS if is_analyze else UNMATCHED_REPLY

    def _delay(self, messages: Sequence[BaseMessage]) -> float:
        """Seconds to pause before replying: only a matched entry's generate call is delayed."""
        question = next(
            (str(m.content) for m in reversed(messages) if isinstance(m, HumanMessage)), ""
        ).lower()
        if any(m.type == "system" and m.content == prompts.ANALYZE_SYSTEM for m in messages):
            return 0
        return next(
            (e.delay_seconds for e in self.script if e.match.lower() in question),
            0,
        )

    def _result(self, messages: Sequence[BaseMessage]) -> ChatResult:
        message = AIMessage(content=self._reply(messages))
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if seconds := self._delay(messages):
            time.sleep(seconds)
        return self._result(messages)

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if seconds := self._delay(messages):
            await asyncio.sleep(seconds)
        return self._result(messages)
