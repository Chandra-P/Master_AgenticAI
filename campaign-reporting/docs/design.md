# Campaign reporting design

## Approved behavior

The owner-approved implementation plan is preserved in implementation-plan.md. This project uses fictional clients only. A Checking account qualifies when its account-open date meets a qualifying upstream match and it has appeared in the funded core extract by the reporting date. Extract inclusion is funding evidence; no deposit indicator/date is fabricated. Preserve observed eligible records in immutable source history even when later active extracts omit them. Count distinct account IDs; count distinct new-member IDs across any qualifying product. Multiple accounts and joint holders must not multiply account counts.

DM uses response_flag=1. Its in-home date is excluded and the next 60 calendar days are included. TU-style digital matches use exposeduserflag=1; a local DM duration does not replace TU attribution. DM/digital categories are mutually exclusive; Both counts once overall. Existing-member Checking accounts remain eligible without a separate quality exception.

CPA is unavailable before day 120 and until both mailings and digital launched. Then use the full $215,000 budget, divided by qualifying Checking accounts; no accounts means unavailable. Budget is 70% DM ($75,250 each drop) and 30% digital ($64,500). Targets: 601 Checking accounts, 605 new members, CPA ceiling $358.17. Two drops target the same 100,000 households; digital reaches 80,000 of those households.

## Fifty-client expansion

Owner requested 50 fictional clients with different dates in 2024 and 2025. There are 25 in each year. Client names and schedules are distinct; all use the confirmed budget/audience/goal template. Digital starts January 15 plus six days per client within each year; first mailing follows seven days later, second after 70 days; digital ends at day 113 and final read is day 144. These relative dates are synthetic implementation choices preserving the approved spacing, not official provider rules. The original 2026 Juniper configuration remains an example/test fixture, not part of the 50-client portfolio.

## Projection

Twenty-four seeded historical synthetic campaigns provide daily cumulative response curves. Match the digital-support configuration before using a cohort. Forecast = observed count / median completion fraction for the reporting age. Lower/upper scenarios use empirical high/low completion fractions. Final is observed count, with a zero-width range. This is an illustrative scenario model, not a validated statistical confidence interval or real Vericast methodology. Never use future records from the current campaign to forecast an earlier read. Forecast members independently before claiming a member finish; current report shows observed members only.

## Local harness versus deployment

SQLite provides a persistent offline workflow demo because Docker and Postgres are unavailable on this host. It is explicitly not a proof of database-role isolation. Postgres schema, service-role grants, row security, session-bound client mapping, and an adapter are provided for a separately provisioned local database. Do not use an owner/superuser connection in application services. Postgres integration tests must pass before calling that profile verified.

The Airflow DAG is a development integration using asset scheduling; it is not a deployed scheduler. Airflow requires a separate metadata database and Linux/container runtime. The local demo invokes the same computation directly. No Airflow uptime or managed deployment has been verified.

## Review and delivery

Run identity hashes the source contents, configuration and rules. Durable LangGraph checkpoints pause for exact-draft review. Approval records the reviewed hash; regeneration clears approval; published runs cannot be edited. A source correction creates a new version. Publication uses exclusive file creation and content hashes, with idempotent retries. Files may be copied after download; local HTML does not provide revocable access by itself.
