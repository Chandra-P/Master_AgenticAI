-- Apply with an administrative database connection. Never expose the service role key.
create table if not exists public.tagalong_state (
 id integer primary key check(id=1),
 state jsonb not null
);
insert into public.tagalong_state values(1,'{"plans":{},"members":{},"actors":{},"proposals":{},"sources":{},"jobs":{}}') on conflict do nothing;
create table if not exists public.tagalong_memberships(plan_id uuid not null, user_id uuid not null references auth.users(id), primary key(plan_id,user_id));
create table if not exists public.tagalong_revisions(plan_id uuid primary key,revision bigint not null);
alter table public.tagalong_state enable row level security;
alter table public.tagalong_memberships enable row level security;
alter table public.tagalong_revisions enable row level security;
revoke all on public.tagalong_state,public.tagalong_memberships,public.tagalong_revisions from anon,authenticated;
grant select on public.tagalong_memberships,public.tagalong_revisions to authenticated;
create policy own_memberships on public.tagalong_memberships for select to authenticated using(user_id=auth.uid());
create policy member_revisions on public.tagalong_revisions for select to authenticated using(exists(select 1 from public.tagalong_memberships m where m.plan_id=tagalong_revisions.plan_id and m.user_id=auth.uid()));
-- Safe to rerun the publication step.
do $$ begin
 if not exists(select 1 from pg_publication_tables where pubname='supabase_realtime' and tablename='tagalong_revisions') then
 alter publication supabase_realtime add table public.tagalong_revisions;
 end if;
end $$;
-- Queryable projections; state aggregate remains the transactional consistency boundary.
create table if not exists public.tagalong_plans(id uuid primary key,owner_id uuid not null,revision bigint not null,document jsonb not null);
create table if not exists public.tagalong_proposals(id uuid primary key,plan_id uuid not null,label text not null,status text not null,document jsonb not null);
create table if not exists public.tagalong_sources(source_key text primary key,plan_id uuid not null,source_id text not null,version bigint not null,deleted boolean not null,document jsonb not null);
create table if not exists public.tagalong_ingestion_jobs(id uuid primary key,source_key text not null,status text not null,attempts integer not null,lease_until double precision not null,document jsonb not null);
alter table public.tagalong_plans enable row level security;
alter table public.tagalong_proposals enable row level security;
alter table public.tagalong_sources enable row level security;
alter table public.tagalong_ingestion_jobs enable row level security;
revoke all on public.tagalong_plans,public.tagalong_proposals,public.tagalong_sources,public.tagalong_ingestion_jobs from anon,authenticated;
