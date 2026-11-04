# Financial rules

## Money and dates

Money is stored in cents and calculated with Python Decimal. Display/API values are strings rounded to cents using ROUND_HALF_UP. Percent changes are rounded to two decimals. Loan payments use the standard fully amortizing monthly-payment formula; APR is interpreted as a nominal annual rate divided by twelve. Zero APR uses principal / months. No APR means no projection.

Every analytics interval is `[start, end)` and also excludes dates after 2026-11-02. “Last month” means October 1 through November 1 excluded. “Last three complete months” means August 1 through November 1 excluded. Month-name questions default to 2026 unless a year is given. Partial current-month values are not extrapolated.

## Ledger conventions

- Positive expense amounts are outflows. Income and refunds are negative-signed entries.
- Income uses transaction_type=income, inverted to positive inflow.
- Expense totals sum expense entries including negative refunds, on the refund posting date.
- Internal transfers, pending, reversed, flagged duplicate copies, inactive/excluded accounts, and future-dated entries are excluded.
- The ledger screen retains diagnostic entries for transparency.
- Missing rows produce null / “no matching data.” Matching zero-valued rows produce measured zero.
- Savings rate = (income − expenses) / income × 100; zero or missing income is undefined, never silently zero percent.
- Largest purchases use positive posted expense amounts; refunds are separate entries. Exactly five are returned when five qualify.
- Costco variants normalize to Costco across the merchant family. Querying a specific alias uses that family; it does not silently restrict to a particular store or channel.
- Recurring schedules carry explicit frequency and evidence. Monthly schedules require three complete months of matching posted charges; annual schedules use explicit billing evidence. Annual prices / 12 are monthly equivalents, not proof of actual monthly cash outflow. No usage claim is made.

## Baseline

October net income $10,000; expenses $6,000; surplus $4,000; savings rate 40%. Expenses: housing $2,800; groceries $900; restaurants $650; utilities $350; subscriptions $250; net hotel $300 ($600 charge less $300 refund); shopping $450; transport $300.

September groceries $800 and restaurants $550; expenses $5,800. Restaurant increase is $100 / 18.18%, not a doubling. Costco totals $2,400 over May–October. Five largest October charges: $2,800, $600, $500, $450, $350. This November’s posted expenses are $2,800; transfers are excluded.

## Scenario model

New income = baseline income × (1 − income reduction / 100).

New surplus = new income − baseline expenses − new monthly payment + canceled monthly equivalents − extra contributions.

Remaining cash = baseline cash − down payment − cash purchase + immediate inflow.

Emergency passes when remaining cash ≥ reserve. Cash flow passes when surplus ≥ 0. Funding passes when remaining cash ≥ 0. Cash earmarks must also fit: remaining cash ≥ emergency reserve + remaining house savings. Overlapping reserves are explicitly flagged.

Baseline cash allocation: $25,000 emergency reserve + $20,000 house earmark + $15,000 unallocated cash. Cash outflows consume unallocated cash first, then house savings; emergency violation is checked independently. An earmark is not an additional asset.

Goal contribution = max(0, surplus), capped at configured monthly house allocation. Months to target = ceiling((target − earmarked savings) / contribution). Already funded means zero months. A positive gap with zero contribution means no finite timeline. Delay is projected months minus baseline months, floored at zero. The initial allowed delay is **two months**, a visible demo assumption requiring confirmation before relying on it.

Extra contributions are separate earmarked savings, so they reduce house contribution availability. They do not disappear as spending, but they are unavailable to the house goal. Immediate inflows are explicit user assumptions, never invented income.

The target date is displayed, while the model reports contribution-count timelines; it does not simulate a particular payday calendar. No interest, investment return, inflation, salary growth, tax change, trade-in, insurance change, registration, dealer fees, or maintenance is invented. Loan-only affordability remains partial evidence.

## Primary comparison

Current offer: $50,000 vehicle; 6.49% APR; 60 months; late fee 5% is not APR.

| Option | Down payment | Monthly payment | Cash left | Monthly surplus | House months | Added delay |
|---|---:|---:|---:|---:|---:|---:|
| Higher down payment | $20,000 | $586.84 | $40,000 | $3,413.16 | 11 | 3 |
| Lower down payment | $10,000 | $782.46 | $50,000 | $3,217.54 | 10 | 2 |
| Postpone | $0 | $0 | $60,000 | $4,000 | 8 | 0 |

The higher down payment consumes $5,000 of house savings and exceeds the default delay allowance. Both financed options preserve the baseline emergency reserve; unknown ownership costs can change the outcome. Passing modeled constraints is not a definitive purchase recommendation.
