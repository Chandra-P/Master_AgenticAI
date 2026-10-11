"""CSV validation and progress calculations for KidSpark."""
from pathlib import Path
import csv
from decimal import Decimal, InvalidOperation

import pandas as pd

COLUMNS = ['learner', 'mission_id', 'mission', 'category', 'completed', 'stars']


def load_missions(path: Path) -> pd.DataFrame:
    """Load mission assignments, rejecting invalid data with a helpful error."""
    try:
        with Path(path).open(encoding='utf-8-sig', newline='') as source:
            reader = csv.reader(source, strict=True)
            header = next(reader)
            rows = []
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    raise ValueError(f'CSV row ending on line {reader.line_num} must have {len(header)} fields.')
                rows.append(row)
        if len(set(header)) != len(header):
            raise ValueError('CSV column names must be unique.')
        df = pd.DataFrame(rows, columns=header, dtype=str)
    except (StopIteration, csv.Error) as exc:
        raise ValueError('The mission CSV needs a header and valid rows.') from exc
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError('Missing CSV columns: ' + ', '.join(sorted(missing)))
    df = df[COLUMNS].copy()
    for column in COLUMNS:
        df[column] = df[column].str.strip()
    for column in COLUMNS[:4]:
        if df[column].eq('').any():
            raise ValueError(f'{column} must not be blank.')
    if df.duplicated(['learner', 'mission_id']).any():
        raise ValueError('Each learner/mission ID pair must be unique.')
    completed = df.completed.str.lower()
    if not completed.isin(['true', 'false']).all():
        raise ValueError('completed must be true or false.')
    df['completed'] = completed.eq('true')
    stars = []
    for text in df.stars:
        try:
            value = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError('stars must be finite nonnegative integers.') from exc
        if not value.is_finite() or value < 0 or value != value.to_integral_value():
            raise ValueError('stars must be finite nonnegative integers.')
        stars.append(int(value))
    # Keep Python integers so sums do not overflow fixed-width integer types.
    df['stars'] = pd.Series(stars, index=df.index, dtype=object)
    return df


def summarize(df: pd.DataFrame) -> dict:
    completed = int(df.completed.sum())
    total = len(df)
    return dict(completed=completed, total=total,
                stars=int(df.loc[df.completed, 'stars'].sum()),
                progress=100 * completed / total if total else 0)


def category_progress(df: pd.DataFrame) -> pd.DataFrame:
    rows = [dict(category=name, **summarize(group))
            for name, group in df.groupby('category', sort=True)]
    return pd.DataFrame(rows, columns=['category', 'completed', 'total', 'progress', 'stars'])


def leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    rows = [dict(learner=name, stars=summary['stars'], completed=summary['completed'])
            for name, group in df.groupby('learner')
            for summary in [summarize(group)]]
    rows.sort(key=lambda row: (-row['stars'], -row['completed'], row['learner']))
    previous = None
    rank = 0
    for position, row in enumerate(rows, 1):
        score = (row['stars'], row['completed'])
        if score != previous:
            rank = position
        row['rank'] = rank
        previous = score
    return pd.DataFrame(rows, columns=['rank', 'learner', 'stars', 'completed'])
