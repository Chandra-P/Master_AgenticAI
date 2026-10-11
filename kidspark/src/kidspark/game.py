"""Game rules independent of Streamlit, clocks, and durable storage."""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
import unicodedata
from uuid import uuid4

from kidspark.challenges import CONTENT_VERSION, Question, select_questions


def normalize_nickname(value: str) -> tuple[str, str]:
    """Return a stable identity and readable display name; reject unusable input."""
    if not isinstance(value, str) or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('Use a nickname without hidden or control characters.')
    display = ' '.join(unicodedata.normalize('NFKC', value).split())
    if not 1 <= len(display) <= 32:
        raise ValueError('Choose a nickname between 1 and 32 characters.')
    return display.casefold(), display


@dataclass
class Round:
    attempt_id: str
    nickname_key: str
    nickname: str
    challenge: str
    level: str
    questions: tuple[Question, ...]
    started_at: str
    started_monotonic: float
    content_version: str = CONTENT_VERSION
    answers: list[dict] = field(default_factory=list)
    cursor: int = 0
    completed_at: str | None = None
    elapsed_seconds: float | None = None

    @property
    def complete(self) -> bool:
        return self.completed_at is not None


def start_round(nickname: str, challenge: str, level: str) -> Round:
    key, display = normalize_nickname(nickname)
    attempt_id = str(uuid4())
    questions = select_questions(challenge, level, attempt_id)
    return Round(attempt_id, key, display, challenge, level, questions,
                 datetime.now(timezone.utc).isoformat(), time.monotonic())


def submit_answer(round: Round, question_id: str, choice_index: int) -> bool:
    """Accept one answer for the current decision; stale/repeated actions are no-ops."""
    if round.complete or len(round.answers) > round.cursor:
        return False
    question = round.questions[round.cursor]
    if question_id != question.id:
        return False
    if type(choice_index) is not int or choice_index not in range(len(question.choices)):
        raise ValueError('Choose one of the three answers before submitting.')
    round.answers.append(dict(question_id=question.id, skill=question.skill,
                              selected_index=choice_index,
                              correct=choice_index == question.correct_index))
    if len(round.answers) == len(round.questions):
        round.completed_at = datetime.now(timezone.utc).isoformat()
        round.elapsed_seconds = max(0, time.monotonic() - round.started_monotonic)
    return True


def advance(round: Round) -> bool:
    """Move past feedback only after the current question has been answered."""
    if round.complete or len(round.answers) != round.cursor + 1:
        return False
    round.cursor += 1
    return True


def completed_result(round: Round) -> dict:
    """Return a detached JSON-compatible result with frozen completion details."""
    if not round.complete or len(round.answers) != 5:
        raise ValueError('Finish all five decisions before saving a result.')
    correct = sum(answer['correct'] for answer in round.answers)
    return dict(attempt_id=round.attempt_id, nickname_key=round.nickname_key,
                nickname=round.nickname, challenge=round.challenge, level=round.level,
                content_version=round.content_version, score=correct * 20,
                correct_count=correct, question_count=5, accuracy=correct / 5 * 100,
                started_at=round.started_at, completed_at=round.completed_at,
                elapsed_seconds=round.elapsed_seconds, answers=deepcopy(round.answers))
