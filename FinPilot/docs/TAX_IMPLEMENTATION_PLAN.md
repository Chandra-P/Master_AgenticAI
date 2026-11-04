# Texas payroll and federal tax planning implementation plan

Goal: add a tested 2026 Texas W-2 planning workflow without changing existing finance behavior.

Architecture: extend SQLite with reviewed payroll facts, confirmed household tax profiles, audit and scenario runs. Extract paystub data from existing validated document chunks; only user-confirmed records enter projections. Use versioned official federal rules and Decimal for every monetary calculation. Connect net payroll cash-flow changes and a tax reserve to the existing goal simulator. Keep OpenAI as a bounded planner and preserve all original golden cases.

Approved scope: U.S./Texas, tax year 2026, single or married filing jointly, workers aged 18–49, one employer per worker, standard deduction, user-confirmed nonrefundable credits, ordinary non-wage income, traditional/Roth 401(k), eligible payroll HSA, regular Medicare, capped Social Security and Additional Medicare. Explicitly exclude filing, actual W-4 submission, self-employment, capital gains/NIIT, AMT, itemized/special deductions, refundable credits, tips/overtime special deductions, catch-ups, equity compensation, and changing states. Estimates remain scope-limited; unsupported or missing data abstains.

Official evidence downloaded: IRS Rev Proc 2025-32 (2026 brackets/deductions), Rev Proc 2025-19 (HSA), IRS 2026 retirement announcement, IRS Publications 15/505/969, SSA contribution base, a Texas constitutional reference (client-rendered shell; statutory text not extracted). Archive checksums and relevant passages in docs/TAX_RULES.md and tax rule JSON.

Synthetic household: Alex and Jordan, two semimonthly jobs, October 31 latest regular paychecks, 20 completed/4 remaining periods. Net deposits total $10,000/month, matching the existing ledger. Combined projected federal taxable wages $144,000; standard deduction $32,200; taxable income $111,800; federal regular income tax $14,020; withholding $11,882.40; balance $2,137.60. Prior-year total tax $13,600 and AGI $145,000, full-year return confirmed. All assumptions synthetic and editable.

Tasks:
- [x] 1. Schema + reviewed paystub contracts: new migration, safe extraction, ownership, explicit confirmation, checksum/duplicate/correction handling, deterministic compatible seed. Tests: upgrade/idempotence, net reconciliation, YTD versus current, unknown fields, hostile lines, tenant boundaries.
- [x] 2. Rule engine: verified year/status rules, progressive income tax, worker-level FICA, withholding projection using latest YTD + remaining regular checks, annual safe-harbor screen, limits and missing data. Tests: bracket boundaries, zero income, cap/Additional Medicare, 90/100/110 percent, less-than-$1000 screen, exhausted checks, unsupported scope, per-person limits.
- [x] 3. Strategies + goals: compare traditional/Roth/HSA/withholding changes, show tax liability versus payment timing, immediate take-home versus economic cost, save audit and goal impacts. Tests: exact examples, no FICA deduction for 401(k), HSA eligibility/limits, no double counting, deterministic repeats.
- [x] 4. API/UI/Copilot: Tax Planning navigation, household review, upload/preview/confirm, paystub evidence, strategy form, assumptions/errors and traces. Tests: ASGI flow, confirmation/revision, frontend states/forms, tax route and provenance.
- [ ] 5. Tax evaluations, independent review, all regression checks, production build, browser journey when runnable, source/archive refresh and documentation. Report exact executed outcomes without claiming unrun checks.

Review focus: current versus YTD double counting; withholding versus tax savings; same dollars counted in both tax reserve and goals; unreviewed/duplicate/corrected paystubs; tax-year and eligibility mismatch; silent assumption of missing inputs. No secrets or real household documents are needed.

Independent review: fixed local-only payroll embedding enforcement, stale results after edits/failures, ambiguous combined Copilot instructions, review-checkbox reset, and employment-selection defaults. Added explicit cafeteria-plan confirmation and tax-rule-year validation.

Final evidence:74 backend tests,10 frontend tests,59 golden cases, formatting/lint/type checks and production build passed. Task5 review/regression/docs/package are implemented; live browser gate remains blocked by local socket permissions, so it is not marked fully verified. See TAX_RELEASE_REPORT.md for exact commands and remaining gates.
