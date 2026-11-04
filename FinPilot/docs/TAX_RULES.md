# 2026 Texas payroll and federal tax rules

This is a **scope-limited planning estimate**, not tax preparation, legal advice, a filed Form 1040, or a completed W-4. Rules are fixed in `backend/finpilot/rules/us_tx_2026.json`, version `us-tx-w2-2026.1`. Other years and unsupported filing situations abstain.

Supported: full-year U.S. tax residents with Texas W-2 wages, single or married filing jointly, workers aged 18–49, one employer per worker, standard deduction, confirmed nonrefundable credits, ordinary non-wage income, and reviewed payroll contribution/withholding assumptions. No state individual income tax is modeled for Texas; property and sales taxes remain separate household costs.

## Source verification

Federal numeric amounts were checked against downloaded official documents. Original bytes, extracted text, URLs and SHA-256 hashes are retained under `artifacts/tax-sources/`. The Texas constitutional link is provided as a legal reference; its fetched HTML is a client-rendered navigation page, not a locally verified copy of the statutory text. Do not treat that cached shell as quotation evidence.

| Rule | 2026 amount / treatment | Official source |
|---|---|---|
| Standard deduction | Single $16,100; MFJ $32,200 | [IRS Rev Proc 2025-32 §3.14](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf) |
| Progressive brackets | Seven rates, 10% through 37%, separate single/MFJ thresholds in rule JSON | [IRS Rev Proc 2025-32 §3.01](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf) |
| Employee 401(k) elective deferrals | $24,500 per worker, traditional + Roth combined; employer match not included in this elective limit | [IRS 2026 retirement limits](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500) |
| HSA | Self-only $4,400; family $8,750; employee + employer contributions count | [IRS Rev Proc 2025-19](https://www.irs.gov/pub/irs-drop/rp-25-19.pdf) |
| Social Security | Employee 6.2%, wage base $184,500 per worker | [IRS Publication 15 (2026)](https://www.irs.gov/publications/p15), [SSA wage base](https://www.ssa.gov/oact/cola/cbb.html) |
| Medicare | Employee 1.45%, no wage cap | [IRS Publication 15](https://www.irs.gov/publications/p15) |
| Additional Medicare | 0.9% on combined Medicare wages above $200,000 single / $250,000 MFJ | [IRS Publication 505](https://www.irs.gov/publications/p505) |
| Employer Additional Medicare withholding | Employer begins at $200,000 for each worker, regardless of joint filing status | [IRS Publication 15 §7](https://www.irs.gov/publications/p15) |
| Annual underpayment screen | Generally 90% of current tax or 100% of eligible prior tax, whichever smaller; 110% prior tax if prior AGI exceeds $150,000 for supported statuses | [IRS Publication 505](https://www.irs.gov/publications/p505) |
| Small balance exception | Less than $1,000 after withholding; estimated payments are not used to manufacture this exception | [IRS Topic 306](https://www.irs.gov/taxtopics/tc306) |
| Texas individual income tax | No individual state income tax; constitutional reference Article VIII §24-a | [Texas constitution reference](https://statutes.capitol.texas.gov/Docs/CN/htm/CN.8.htm) |

HSA eligibility must be confirmed. The modeled household limit is prorated by confirmed eligible months, without the last-month rule or catch-ups. Additional payroll HSA tax savings also require explicit confirmation of a pre-tax cafeteria plan; direct after-tax HSA deposits are not silently given FICA savings. Two separate self-only HSA owners are outside this household coverage model.

## Data conventions

Paystub money is validated as finite Decimal amounts with at most two fractional digits, stored in confirmed JSON records as decimal strings. Extracted values remain inactive until explicit review. Blank means unknown; it is never silently converted to zero. Gross minus employee contributions, other deductions and payroll withholding must reconcile to net pay within two cents for both current and YTD amounts. Wage bases are explicit fields, not inferred from net income.

Only the latest confirmed, non-superseded, eligible paystub per employment is used. The calculation is:

`projected amount = latest YTD amount + latest regular current amount × reviewed remaining paychecks`

It is **not** the sum of several YTD records and is not YTD multiplied by a blind annualization factor. A reviewed next-pay date is required while checks remain. If that date has arrived without a newer confirmed stub, future-change simulations abstain; past checks cannot receive retroactive contributions. Additional staleness checks also apply relative to pay frequency. Past bonuses may already be included in YTD totals; future bonuses or salary changes are not invented.

Duplicate pay date/employment records cannot activate twice. A correction must explicitly name the same owned employment/pay date; the previous record is retained as superseded. Audit records preserve extraction, user-confirmed edits, corrections, and tax-profile revision changes. User edits are confirmed facts, not a claim that the source document contained the edited value.

## Calculation and timing

Federal taxable wages already reflect recorded pre-tax wage exclusions. Baseline retirement/HSA contributions are not deducted again. Extra traditional contributions reduce future federal wages but not FICA wages. Extra Roth contributions reduce take-home pay but not taxable wages. Eligible extra cafeteria-plan HSA contributions reduce federal, Social Security and Medicare wage bases, subject to caps and eligibility.

Regular federal tax is progressive bracket tax less nonrefundable credits, floored at zero. Additional Medicare liability is calculated at the household filing threshold; its withholding is separately projected at the employer threshold. Regular Social Security and Medicare payments are not subtracted again from the income-tax balance.

`federal settlement = regular federal income tax + Additional Medicare liability − federal income withholding − Additional Medicare withholding − estimated federal payments`

Positive settlement becomes an estimated balance due; negative settlement becomes a projected refund. Refunds are not added to current cash before receipt.

Changing withholding changes payment timing, not tax liability. The scenario deliberately holds federal income withholding constant except for explicit extra withholding. Real payroll may automatically recompute it when pre-tax deductions change; the modeled take-home effect is a fixed-withholding scenario, not a guaranteed next-paycheck forecast. Immediate payroll-tax withholding reductions can affect the next paychecks, including the separate employer Additional Medicare threshold.

`economic after-tax cost of extra contributions = extra contributions − estimated income-tax reduction − estimated payroll-tax reduction`

This economic cost excludes extra withholding, which is a payment timing change. It must not be mislabeled as immediate take-home cost.

The annual safe-harbor result is a screen, not a penalty calculation. Unknown prior-year information stays unknown. Installment deadlines, annualized-income exceptions, and special rules are not implemented; a late estimated payment may not cure earlier underpayment. Per-paycheck illustrations round up to cents across remaining household paychecks. No remaining checks means no per-paycheck adjustment is invented.

## Goal connection

A positive projected balance is earmarked from existing cash. The existing simulator applies the **net** average monthly payroll cash reduction to the surplus available for the house, instead of subtracting both gross contributions and their net cost. It checks the emergency reserve and non-overlapping house earmark. The house projection assumes the monthly rate continues; the tax projection covers only the remaining 2026 checks.

## Synthetic worked example

Alex: gross $4,000/check; traditional 401(k) $400; payroll HSA $100; federal wages $3,500; federal withholding $201.65; Social Security $241.80; Medicare $56.55; take-home $3,000. Jordan: gross $2,700; traditional $200; federal wages $2,500; federal withholding $293.45; Social Security $167.40; Medicare $39.15; take-home $2,000. Both have 24 annual paychecks, 20 completed and four remaining, with the next reviewed payday November15. This exactly matches the existing $10,000 monthly net-income fixture.

Projected federal wages: $144,000. Standard deduction: $32,200. Taxable income: $111,800. Bracket tax: $2,480 + $9,120 + $2,420 = $14,020. Federal withholding: $11,882.40. Projected balance: $2,137.60. Current-year 90% target: $12,618; shortfall $735.60, before installment-timing considerations.

Alex adding $250 traditional per remaining check adds $1,000 of contributions: federal tax reduction $220, no FICA reduction, immediate take-home reduction $1,000, economic after-tax cost $780. Adding $100 eligible payroll HSA instead adds $400: federal reduction $88, FICA reduction $30.60, immediate take-home reduction $369.40, economic cost $281.40. Adding $100 withholding per check reduces the projected balance by $400 but produces no tax saving.

## Exclusions

No self-employment, capital gains, NIIT, AMT, itemized deductions, special tips/overtime/car-loan-interest deductions, refundable credits, retirement catch-ups, stock compensation, changing states, nonresident returns, benefits optimization, or employer match strategy. Annual bracket-schedule estimates use cents; actual return tax tables and whole-dollar conventions may differ. Missing/out-of-scope facts require correction or qualified professional review.
