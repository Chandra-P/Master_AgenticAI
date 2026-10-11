"""Progress derived exclusively from saved completed decisions."""
from collections import defaultdict
from datetime import datetime
import pandas as pd
from kidspark.challenges import CHALLENGES, LEVELS


def summarize_attempts(attempts: list[dict]) -> dict:
    correct = sum(a['correct_count'] for a in attempts)
    total = sum(a['question_count'] for a in attempts)
    return dict(rounds=len(attempts), challenges=len({a['challenge'] for a in attempts}),
                score=sum(a['score'] for a in attempts), correct=correct, total=total,
                accuracy=100 * correct / total if total else 0)


def skill_accuracy(attempts: list[dict]) -> pd.DataFrame:
    """Weight each answered decision equally, even across different sample sizes."""
    counts = defaultdict(lambda: [0, 0])
    for attempt in attempts:
        for answer in attempt['answers']:
            counts[answer['skill']][0] += int(answer['correct'])
            counts[answer['skill']][1] += 1
    return pd.DataFrame([dict(skill=skill, correct=correct, total=total,
                              accuracy=100 * correct / total)
                         for skill, (correct, total) in sorted(counts.items())],
                        columns=['skill', 'correct', 'total', 'accuracy'])


def suggest_challenge(attempts: list[dict], level: str) -> tuple[str, str]:
    """Recommend an untried round, then the weakest challenge at this school level."""
    if level not in LEVELS:
        raise ValueError('Choose a supported school level.')
    relevant = [a for a in attempts if a['level'] == level]
    tried = {a['challenge'] for a in relevant}
    for challenge in CHALLENGES:
        if challenge not in tried:
            return challenge, f'Try a new adventure at {level.lower()} level.'
    def accuracy(challenge: str) -> float:
        return summarize_attempts([a for a in relevant if a['challenge'] == challenge])['accuracy']
    challenge = min(CHALLENGES, key=accuracy)
    return challenge, f'Practice these skills again: your saved accuracy here is {accuracy(challenge):.0f}% at {level.lower()} level.'


def challenge_leaderboard(best_scores: list[dict], challenge: str | None = None) -> pd.DataFrame:
    """Rank best per-challenge scores; repeat attempts do not add leaderboard points."""
    if challenge is not None and challenge not in CHALLENGES:
        raise ValueError('Choose a supported challenge.')
    students = {}
    for row in best_scores:
        if row['challenge'] not in CHALLENGES:
            continue
        if challenge and row['challenge'] != challenge:
            continue
        student = students.setdefault(row['nickname_key'], {'name': row['nickname'], 'scores': {}})
        scores = student['scores']
        scores[row['challenge']] = max(scores.get(row['challenge'], 0), row['best_score'])
    rows = [{'Nickname': value['name'], 'Best points': sum(value['scores'].values()),
             'Challenges played': len(value['scores'])} for value in students.values()
            if challenge is not None or len(value['scores']) == len(CHALLENGES)]
    rows.sort(key=lambda row: (-row['Best points'], -row['Challenges played'], row['Nickname'].casefold()))
    previous = None
    rank = 0
    for position, row in enumerate(rows, 1):
        score = row['Best points'], row['Challenges played']
        if score != previous:
            rank = position
        row['Rank'] = rank
        previous = score
    return pd.DataFrame(rows, columns=['Rank', 'Nickname', 'Best points', 'Challenges played'])


def challenge_progress(attempts: list[dict], level: str) -> list[dict]:
    """Compare saved first/latest/best scores within a school level, never mastery."""
    if level not in LEVELS:
        raise ValueError('Choose a supported school level.')
    cards = []
    for challenge in CHALLENGES:
        played = sorted((a for a in attempts if a['level'] == level and a['challenge'] == challenge),
                        key=lambda a: (datetime.fromisoformat(a['completed_at']), a['attempt_id']))
        first = played[0]['score'] if played else None
        latest = played[-1]['score'] if played else None
        cards.append(dict(challenge=challenge, rounds=len(played), first=first, latest=latest,
                          best=max(a['score'] for a in played) if played else None,
                          change=latest - first if len(played) > 1 else None))
    return cards
