"""Atomic SQLite writes and nickname-filtered history; no shared connections."""
from contextlib import closing
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import sqlite3
from uuid import UUID

from kidspark.challenges import LEVELS, question_bank
from kidspark.game import normalize_nickname

FIELDS = ('attempt_id', 'nickname_key', 'nickname', 'challenge', 'level',
          'content_version', 'score', 'correct_count', 'question_count',
          'accuracy', 'started_at', 'completed_at', 'elapsed_seconds')
SCHEMA = '''CREATE TABLE IF NOT EXISTS attempts (
    attempt_id TEXT PRIMARY KEY,
    nickname_key TEXT NOT NULL,
    nickname TEXT NOT NULL,
    challenge TEXT NOT NULL,
    level TEXT NOT NULL,
    content_version TEXT NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
    correct_count INTEGER NOT NULL CHECK(correct_count BETWEEN 0 AND 5),
    question_count INTEGER NOT NULL CHECK(question_count = 5),
    accuracy REAL NOT NULL CHECK(accuracy BETWEEN 0 AND 100),
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    elapsed_seconds REAL NOT NULL CHECK(elapsed_seconds >= 0),
    answers_json TEXT NOT NULL
)'''


def _validate(result: dict) -> None:
    """Reject incomplete or inconsistent data at the durable write boundary."""
    try:
        if set(result) != set(FIELDS) | {'answers'}:
            raise ValueError('Unexpected result fields.')
        UUID(result['attempt_id'])
        key, display = normalize_nickname(result['nickname'])
        if key != result['nickname_key'] or display != result['nickname']:
            raise ValueError('Nickname identity does not match.')
        version = result['content_version']
        questions = question_bank(result['challenge'], result['level'], version)
        by_id = {q.id: q for q in questions}
        answers = result['answers']
        if len(answers) != 5 or type(result['question_count']) is not int or result['question_count'] != 5:
            raise ValueError('Finish all five decisions before saving.')
        objectives = set()
        for position, answer in enumerate(answers):
            q = by_id.get(answer['question_id'])
            if q is None or q.objective in objectives:
                raise ValueError('Use one question from each round objective.')
            if version == '1' and q.id != questions[position].id:
                raise ValueError('Historical question order does not match.')
            objectives.add(q.objective)
            index = answer['selected_index']
            if (set(answer) != {'question_id', 'skill', 'selected_index', 'correct'}
                    or answer['question_id'] != q.id or answer['skill'] != q.skill
                    or type(index) is not int or index not in range(3)
                    or type(answer['correct']) is not bool
                    or answer['correct'] != (index == q.correct_index)):
                raise ValueError('Answer details do not match the round.')
        correct = sum(a['correct'] for a in answers)
        if (type(result['correct_count']) is not int or result['correct_count'] != correct
                or type(result['score']) is not int or result['score'] != correct * 20
                or type(result['accuracy']) not in (int, float) or result['accuracy'] != correct * 20):
            raise ValueError('Result totals do not match the answers.')
        elapsed = result['elapsed_seconds']
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('Duration must be finite and nonnegative.')
        started, completed = (datetime.fromisoformat(result[name]) for name in ('started_at', 'completed_at'))
        if any(d.utcoffset() != timedelta(0) for d in (started, completed)) or completed < started:
            raise ValueError('Completion times must be ordered UTC timestamps.')
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError('The completed result is invalid.') from exc


def _connection(path: Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(SCHEMA)
        connection.execute('CREATE INDEX IF NOT EXISTS student_history ON attempts(nickname_key, completed_at)')
        connection.commit()
    except Exception:
        connection.close()
        raise
    return connection


def _decode(row: sqlite3.Row) -> dict:
    return {**{key: row[key] for key in FIELDS}, 'answers': json.loads(row['answers_json'])}


def save_attempt(path: Path, result: dict) -> bool:
    """Insert once, safely retry identical data, and reject ID reuse with different data."""
    _validate(result)
    with closing(_connection(path)) as connection, connection:
        connection.execute('BEGIN IMMEDIATE')
        existing = connection.execute('SELECT * FROM attempts WHERE attempt_id = ?',
                                      (result['attempt_id'],)).fetchone()
        if existing:
            if _decode(existing) != result:
                raise ValueError('This attempt ID already belongs to a different result.')
            return False
        columns = ', '.join((*FIELDS, 'answers_json'))
        placeholders = ', '.join('?' for _ in range(len(FIELDS) + 1))
        connection.execute(f'INSERT INTO attempts ({columns}) VALUES ({placeholders})',
                           tuple(result[key] for key in FIELDS) + (json.dumps(result['answers']),))
    return True


def load_attempts(path: Path, nickname: str) -> list[dict]:
    """Read only the selected profile, including after a new app/server session."""
    key, _ = normalize_nickname(nickname)
    with closing(_connection(path)) as connection:
        rows = connection.execute('SELECT * FROM attempts WHERE nickname_key = ? '
                                  'ORDER BY completed_at, attempt_id', (key,)).fetchall()
        return [_decode(row) for row in rows]


def load_best_scores(path: Path, level: str) -> list[dict]:
    """Return public nickname/score summaries only; never expose other students' answers."""
    if level not in LEVELS:
        raise ValueError('Choose a supported school level.')
    with closing(_connection(path)) as connection:
        rows = connection.execute(
            'SELECT nickname_key, MIN(nickname) AS nickname, challenge, MAX(score) AS best_score '
            'FROM attempts WHERE level = ? GROUP BY nickname_key, challenge', (level,)).fetchall()
        return [dict(row) for row in rows]
