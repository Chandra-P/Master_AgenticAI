-- Additive, backend-only projection. Existing aggregate remains authoritative.
create table if not exists public.tagalong_coordination (
 plan_id uuid primary key references public.tagalong_plans(id),
 plan_revision bigint not null,
 status text not null check(status in ('WAITING_FOR_DATE','WAITING_FOR_VOTES','WAITING_FOR_LOCATION','READY_TO_FINALIZE','ACTIVE','COMPLETED','STALLED')),
 health smallint not null check(health between 0 and 100),
 last_activity_at timestamptz not null default now(),
 document jsonb not null
);
alter table public.tagalong_coordination enable row level security;
revoke all on public.tagalong_coordination from anon,authenticated;
comment on table public.tagalong_coordination is 'Derived coordination summaries, decisions, questions and recommendations; API membership checks required.';
