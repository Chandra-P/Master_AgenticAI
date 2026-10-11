# KidSpark learning content

KidSpark offers ninety authored questions: three variants for each of five
objectives in three real-life challenges at two school levels. Each round
selects one variant per objective, with five decisions, three choices, a free hint,
and an explanation. Story context connects the decisions, but every question
states its own prices, budget, or message so a wrong answer cannot break the
next question.

## Student experience

Smart Shopping helps a supply squad pack for a school outing. Spot the Scam
helps a fictional friend, Sam, check suspicious messages. Plan an Event asks a
celebration crew to make thoughtful choices for a class event.

Each round starts with a simpler decision. Middle school questions use familiar
amounts and clear clues; high school questions add a second calculation step or
closer evaluation of evidence. Short fact panels put the necessary information
above one direct question. There are no speed bonuses or countdowns.
A calculator and scratch paper are welcome. Hints cost no points.
The optional leaderboard compares best scores within the same school level;
repeated rounds cannot accumulate extra leaderboard points.
Overall ranking requires all three challenges. Every finished challenge earns
a completion badge, including zero-score rounds. Rankings default to hidden.

Correct feedback celebrates useful reasoning; incorrect feedback encourages
the student to inspect the explanation. Every completed round earns a finish
message and a concrete takeaway, including when its score is low.

## Reviewed answer key

The original question source is `src/kidspark/challenges.py`; additional literal
variants are in `src/kidspark/question_variants.py`. New rounds use content
version `2`; the archived version-1 bank remains available for existing results.
The following calculations and reasoning describe the original variants.

| Round | Five correct decisions |
| --- | --- |
| Shopping, middle school | 4 pencils for $2: $0.50 each versus $1; 2 liters for $4: $2/liter versus $3; $10 less 20% = $8; $5 fruit plus $6 crackers = $11 within $12; 4 bars for $5 meet the need within $6 even though the larger pack has a better unit price. |
| Shopping, high school | 2 liters for $4: $2/liter versus $3; 20% of $30 saves $6 versus $5; $40 less 25%, then less 10% = $30 × 0.9 = $27; $20 plus stated 5% tax = $21; Store B costs $24 delivered versus Store A at $26, within a $25 budget. |
| Scam, middle school | Pause and ask a trusted adult about a paid surprise prize; keep a game password private; check an outing announcement through the usual teacher channel; seek evidence for a sweeping snack claim; open the official game app directly to check an urgent account message. |
| Scam, high school | Independently verify a changed school payment request; check an account through the official app or known address rather than a message link; seek independent evidence for a sponsored claim; check a screenshot's original source, date, and context; keep a one-time sign-in code private and contact official support directly. |
| Event, middle school | $15 room + $10 supplies = $25 within $30; 10 snacks × $2 = $20; $50 less $10 reserve = $40; a $20 inclusive package beats $18 + $5 = $23; $60 − ($20 + $15 + $10) = $15 left. |
| Event, high school | $30 room + 20 × $2 supplies = $70; $50 inclusive vendor beats $45 + $8 = $53; $80 less 25% = $60; $100 less 10% reserve = $90; $60 divided among 20 tickets = $3 each. |

All message scenarios are explicitly fictional and contain no suspicious URLs
to click. They encourage independent checking and help from a trusted adult;
they do not ask students to investigate real scams or submit personal messages.
Sponsored content is not labeled automatically false: students are prompted to
look for evidence rather than relying on popularity or sales promises.

## Skills and progress

The recorded skill labels are Unit prices, Discounts, Budgeting, Verification,
Privacy, Evaluating claims, and Event planning. Each correct decision contributes
20 points. A round with three correct decisions scores 60/100 and has 60%
accuracy. Overall and skill accuracy use the number of correct decisions
divided by the number answered across completed rounds.

The app stores the actual selected choice, correctness, question ID, skill, and
content version for each decision. Progress shows only real saved attempts. The original fictional CSV dashboard
is no longer part of the application.

## Content maintenance

When changing the question bank, review numeric assumptions and distractors,
ensure choices are unique, and keep hints useful without revealing the option.
Increment the content version for meaningful answer changes and extend storage
compatibility before accepting new versions. Add tests for question validity
and manually review each calculation and explanation.
The readability update keeps version `1`: question IDs, skills, correct-choice
indices, and scoring are unchanged. Scenario wording and choice labels are
simplified. Automated checks enforce short prompts and bounded fact panels.
The subsequent fair-practice update adds version `2`. Numeric variants use
double or triple the monetary amounts while preserving quantities, rates, and
calculation steps. For example, four pencils for $4 versus six for $12 compares
$1 versus $2 each. Percentage rates and cents-per-dollar rates stay unchanged.
Scam variants change the fictional context while preserving the checking skill.
Selection keeps the introductory objective first and shuffles the other four;
it does not shuffle answer choices or change questions during a round.

## Difficulty rubric

Middle-school variants use familiar amounts, direct clues, and short arithmetic
with stated facts. High-school variants add discount/tax steps or comparison of
sources and missing context. Variants of the same objective retain the same
reasoning steps and reading limits. Challenges each contain five equally scored
decisions. These authored constraints do not establish empirically equal
difficulty; student and educator feedback is still needed before calibration.
Randomization can reduce memorization but cannot eliminate it or prove mastery.

The initial content has an author-level arithmetic and wording review, plus
automated validity and full-round checks. It has not been evaluated with
students or an educator, and is not claimed to be age-validated. Such feedback
should guide reading load and difficulty in a later iteration.
