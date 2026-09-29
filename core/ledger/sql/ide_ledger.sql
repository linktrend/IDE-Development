-- ide_ledger: IDE Development Program Ledger (v3, Wave 0.5).
--
-- Authored in linktrend/IDE-Development; applied to the Platform Supabase
-- project only through LiNKplatform's migration flow (Wave 3.1). Never apply
-- this file by hand to a shared database.
--
-- Access model:
--   * All tables are private to the schema owner (no grants, RLS enabled, no
--     policies), so PostgREST roles and PUBLIC see nothing.
--   * Every read and write goes through SECURITY DEFINER RPC functions with an
--     empty search_path and fully qualified names.
--   * Role ide_ledger_orchestrator gets USAGE on the schema and EXECUTE on the
--     public RPC functions only. It is NOLOGIN here; the Platform migration
--     flow creates the login credential and grants membership out of band so
--     no password ever lives in a repository.
--
-- The file is idempotent: re-applying it must succeed and change nothing.

begin;

create schema if not exists ide_ledger;
revoke all on schema ide_ledger from public;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'ide_ledger_orchestrator') then
    create role ide_ledger_orchestrator nologin noinherit;
  end if;
end
$$;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

-- One row per repo. The prefix builds Issue IDs (<prefix>-<n>) and branches
-- (issue/<prefix>-<n>-<slug>).
create table if not exists ide_ledger.repo (
  prefix       text primary key check (prefix ~ '^[A-Z][A-Z0-9]{1,9}$'),
  repo         text not null unique check (repo ~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'),
  next_number  integer not null default 1 check (next_number >= 1),
  created_at   timestamptz not null default now()
);

-- Accountable owners (a Cursor Project, an orchestrator, or the Principal).
create table if not exists ide_ledger.owner (
  id            text primary key check (id ~ '^[a-z0-9][a-z0-9:._-]{1,79}$'),
  kind          text not null check (kind in ('project', 'orchestrator', 'principal', 'external')),
  display_name  text not null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table if not exists ide_ledger.phase (
  id                   bigint generated always as identity primary key,
  prefix               text not null references ide_ledger.repo (prefix),
  phase_key            text not null check (phase_key ~ '^[0-9A-Za-z][0-9A-Za-z._-]{0,31}$'),
  title                text not null,
  state                text not null default 'planned'
                       check (state in ('planned', 'active', 'packaged', 'merged', 'done', 'cancelled')),
  owner_id             text references ide_ledger.owner (id),
  github_issue_number  integer check (github_issue_number > 0),
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  unique (prefix, phase_key)
);

create table if not exists ide_ledger.issue (
  id           text primary key,
  prefix       text not null references ide_ledger.repo (prefix),
  number       integer not null check (number >= 1),
  phase_id     bigint references ide_ledger.phase (id),
  title        text not null,
  slug         text not null check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and length(slug) <= 60),
  state        text not null default 'planned'
               check (state in ('planned', 'ready', 'in_progress', 'blocked', 'in_review', 'done', 'cancelled')),
  owner_id     text not null references ide_ledger.owner (id),
  repair_rung  integer not null default 0 check (repair_rung between 0 and 3),
  branch       text generated always as ('issue/' || id || '-' || slug) stored,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  unique (prefix, number),
  check (id = prefix || '-' || number::text)
);

create table if not exists ide_ledger.issue_dependency (
  issue_id       text not null references ide_ledger.issue (id),
  depends_on_id  text not null references ide_ledger.issue (id),
  created_at     timestamptz not null default now(),
  primary key (issue_id, depends_on_id),
  check (issue_id <> depends_on_id)
);

-- One row per execution attempt. requested_model is what we asked for;
-- self_reported_model is what the agent said it was (providers do not report
-- the model that actually ran).
create table if not exists ide_ledger.run (
  id                   bigint generated always as identity primary key,
  run_key              text not null unique check (length(run_key) between 8 and 80),
  issue_id             text not null references ide_ledger.issue (id),
  attempt              integer not null check (attempt >= 1),
  executor             text not null
                       check (executor in ('codex-cli', 'cursor-002', 'cursor-001-subagent', 'orchestrator', 'other')),
  requested_model      text not null,
  reasoning_effort     text,
  self_reported_model  text,
  repair_rung          integer not null default 0 check (repair_rung between 0 and 3),
  external_ref         text,
  branch               text,
  head_sha             text check (head_sha ~ '^[0-9a-f]{7,40}$'),
  result               text not null default 'running'
                       check (result in ('running', 'success', 'failure', 'stalled', 'cancelled')),
  failure_summary      text,
  cost_usd             numeric(10, 4) check (cost_usd >= 0),
  started_at           timestamptz not null default now(),
  ended_at             timestamptz,
  unique (issue_id, attempt),
  check ((result = 'running') = (ended_at is null)),
  check (ended_at is null or ended_at >= started_at)
);

create table if not exists ide_ledger.decision (
  id          bigint generated always as identity primary key,
  prefix      text not null references ide_ledger.repo (prefix),
  issue_id    text references ide_ledger.issue (id),
  phase_id    bigint references ide_ledger.phase (id),
  question    text not null,
  decision    text not null,
  rationale   text,
  decided_by  text not null references ide_ledger.owner (id),
  decided_at  timestamptz not null default now()
);

create table if not exists ide_ledger.exception (
  id           bigint generated always as identity primary key,
  prefix       text not null references ide_ledger.repo (prefix),
  issue_id     text references ide_ledger.issue (id),
  run_id       bigint references ide_ledger.run (id),
  kind         text not null
               check (kind in ('stalled_run', 'repeated_failure', 'unpushed_work', 'auth_failure',
                               'allowance_exhausted', 'ci_failure', 'review_rejected', 'escalation', 'other')),
  detail       text not null,
  status       text not null default 'open' check (status in ('open', 'resolved', 'dismissed')),
  resolution   text,
  raised_at    timestamptz not null default now(),
  resolved_at  timestamptz,
  check ((status = 'open') = (resolved_at is null))
);

create table if not exists ide_ledger.audit_log (
  id         bigint generated always as identity primary key,
  at         timestamptz not null default now(),
  actor      text not null default session_user,
  action     text not null,
  entity     text not null,
  entity_id  text not null,
  payload    jsonb not null default '{}'::jsonb
);

create index if not exists issue_phase_idx on ide_ledger.issue (phase_id);
create index if not exists issue_state_idx on ide_ledger.issue (state);
create index if not exists run_issue_idx on ide_ledger.run (issue_id);
create index if not exists run_open_idx on ide_ledger.run (started_at) where result = 'running';
create index if not exists exception_open_idx on ide_ledger.exception (prefix) where status = 'open';

do $$
declare
  t text;
begin
  foreach t in array array['repo', 'owner', 'phase', 'issue', 'issue_dependency', 'run',
                           'decision', 'exception', 'audit_log'] loop
    execute format('alter table ide_ledger.%I enable row level security', t);
    execute format('revoke all on table ide_ledger.%I from public', t);
  end loop;
end
$$;

-- ---------------------------------------------------------------------------
-- Internal helpers (never granted)
-- ---------------------------------------------------------------------------

create or replace function ide_ledger._audit(p_action text, p_entity text, p_entity_id text, p_payload jsonb)
returns void
language sql
security definer
set search_path = ''
as $$
  insert into ide_ledger.audit_log (action, entity, entity_id, payload)
  values (p_action, p_entity, p_entity_id, coalesce(p_payload, '{}'::jsonb));
$$;

create or replace function ide_ledger._phase_id(p_prefix text, p_phase_key text)
returns bigint
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_id bigint;
begin
  if p_phase_key is null then
    return null;
  end if;
  select id into v_id from ide_ledger.phase where prefix = p_prefix and phase_key = p_phase_key;
  if v_id is null then
    raise exception 'unknown phase %/%', p_prefix, p_phase_key using errcode = 'P0002';
  end if;
  return v_id;
end
$$;

-- ---------------------------------------------------------------------------
-- Write RPCs
-- ---------------------------------------------------------------------------

create or replace function ide_ledger.register_repo(p_prefix text, p_repo text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into ide_ledger.repo (prefix, repo) values (p_prefix, p_repo)
  on conflict (prefix) do nothing;
  if not exists (select 1 from ide_ledger.repo where prefix = p_prefix and repo = p_repo) then
    raise exception 'prefix % is already registered to another repo', p_prefix using errcode = '23505';
  end if;
  perform ide_ledger._audit('register_repo', 'repo', p_prefix, jsonb_build_object('repo', p_repo));
  return p_prefix;
end
$$;

create or replace function ide_ledger.upsert_owner(p_id text, p_kind text, p_display_name text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into ide_ledger.owner (id, kind, display_name) values (p_id, p_kind, p_display_name)
  on conflict (id) do update
    set kind = excluded.kind, display_name = excluded.display_name, updated_at = now();
  perform ide_ledger._audit('upsert_owner', 'owner', p_id,
                            jsonb_build_object('kind', p_kind, 'display_name', p_display_name));
  return p_id;
end
$$;

create or replace function ide_ledger.upsert_phase(
  p_prefix text,
  p_phase_key text,
  p_title text,
  p_state text default 'planned',
  p_owner_id text default null,
  p_github_issue_number integer default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_id bigint;
begin
  insert into ide_ledger.phase (prefix, phase_key, title, state, owner_id, github_issue_number)
  values (p_prefix, p_phase_key, p_title, p_state, p_owner_id, p_github_issue_number)
  on conflict (prefix, phase_key) do update
    set title = excluded.title,
        state = excluded.state,
        owner_id = coalesce(excluded.owner_id, ide_ledger.phase.owner_id),
        github_issue_number = coalesce(excluded.github_issue_number, ide_ledger.phase.github_issue_number),
        updated_at = now()
  returning id into v_id;
  perform ide_ledger._audit('upsert_phase', 'phase', p_prefix || '/' || p_phase_key,
                            jsonb_build_object('state', p_state, 'github_issue_number', p_github_issue_number));
  return v_id;
end
$$;

-- Allocates the next <prefix>-<n> unless p_number is given (used when
-- importing IDs already assigned during the pilot).
create or replace function ide_ledger.create_issue(
  p_prefix text,
  p_title text,
  p_slug text,
  p_owner_id text,
  p_phase_key text default null,
  p_state text default 'planned',
  p_number integer default null
)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_number integer;
  v_id text;
begin
  if p_number is null then
    update ide_ledger.repo set next_number = next_number + 1
    where prefix = p_prefix
    returning next_number - 1 into v_number;
  else
    update ide_ledger.repo set next_number = greatest(next_number, p_number + 1)
    where prefix = p_prefix
    returning p_number into v_number;
  end if;
  if v_number is null then
    raise exception 'unknown repo prefix %', p_prefix using errcode = 'P0002';
  end if;
  v_id := p_prefix || '-' || v_number::text;
  insert into ide_ledger.issue (id, prefix, number, phase_id, title, slug, state, owner_id)
  values (v_id, p_prefix, v_number, ide_ledger._phase_id(p_prefix, p_phase_key),
          p_title, p_slug, p_state, p_owner_id);
  perform ide_ledger._audit('create_issue', 'issue', v_id,
                            jsonb_build_object('phase', p_phase_key, 'owner', p_owner_id, 'state', p_state));
  return v_id;
end
$$;

create or replace function ide_ledger.set_issue_state(p_issue_id text, p_state text, p_note text default null)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update ide_ledger.issue set state = p_state, updated_at = now() where id = p_issue_id;
  if not found then
    raise exception 'unknown issue %', p_issue_id using errcode = 'P0002';
  end if;
  perform ide_ledger._audit('set_issue_state', 'issue', p_issue_id,
                            jsonb_build_object('state', p_state, 'note', p_note));
end
$$;

create or replace function ide_ledger.set_issue_owner(p_issue_id text, p_owner_id text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update ide_ledger.issue set owner_id = p_owner_id, updated_at = now() where id = p_issue_id;
  if not found then
    raise exception 'unknown issue %', p_issue_id using errcode = 'P0002';
  end if;
  perform ide_ledger._audit('set_issue_owner', 'issue', p_issue_id, jsonb_build_object('owner', p_owner_id));
end
$$;

create or replace function ide_ledger.set_issue_phase(p_issue_id text, p_phase_key text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update ide_ledger.issue
     set phase_id = ide_ledger._phase_id(prefix, p_phase_key), updated_at = now()
   where id = p_issue_id;
  if not found then
    raise exception 'unknown issue %', p_issue_id using errcode = 'P0002';
  end if;
  perform ide_ledger._audit('set_issue_phase', 'issue', p_issue_id, jsonb_build_object('phase', p_phase_key));
end
$$;

-- Rejects edges that would create a dependency cycle.
create or replace function ide_ledger.add_dependency(p_issue_id text, p_depends_on_id text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if exists (
    with recursive reach(id) as (
      select p_depends_on_id
      union
      select d.depends_on_id from ide_ledger.issue_dependency d join reach r on d.issue_id = r.id
    )
    select 1 from reach where id = p_issue_id
  ) then
    raise exception 'dependency % -> % would create a cycle', p_issue_id, p_depends_on_id
      using errcode = '23514';
  end if;
  insert into ide_ledger.issue_dependency (issue_id, depends_on_id)
  values (p_issue_id, p_depends_on_id)
  on conflict do nothing;
  perform ide_ledger._audit('add_dependency', 'issue', p_issue_id, jsonb_build_object('depends_on', p_depends_on_id));
end
$$;

create or replace function ide_ledger.remove_dependency(p_issue_id text, p_depends_on_id text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from ide_ledger.issue_dependency where issue_id = p_issue_id and depends_on_id = p_depends_on_id;
  perform ide_ledger._audit('remove_dependency', 'issue', p_issue_id,
                            jsonb_build_object('depends_on', p_depends_on_id));
end
$$;

-- Opens an attempt. Idempotent on p_run_key so a retried call or a run-log
-- import never creates a duplicate row. Also moves the Issue to in_progress
-- and records the repair rung.
create or replace function ide_ledger.start_run(
  p_run_key text,
  p_issue_id text,
  p_executor text,
  p_requested_model text,
  p_reasoning_effort text default null,
  p_repair_rung integer default 0,
  p_branch text default null,
  p_external_ref text default null,
  p_started_at timestamptz default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_id bigint;
  v_attempt integer;
begin
  select id into v_id from ide_ledger.run where run_key = p_run_key;
  if v_id is not null then
    return v_id;
  end if;
  perform 1 from ide_ledger.issue where id = p_issue_id for update;
  if not found then
    raise exception 'unknown issue %', p_issue_id using errcode = 'P0002';
  end if;
  select coalesce(max(attempt), 0) + 1 into v_attempt from ide_ledger.run where issue_id = p_issue_id;
  insert into ide_ledger.run (run_key, issue_id, attempt, executor, requested_model, reasoning_effort,
                              repair_rung, branch, external_ref, started_at)
  values (p_run_key, p_issue_id, v_attempt, p_executor, p_requested_model, p_reasoning_effort,
          p_repair_rung, p_branch, p_external_ref, coalesce(p_started_at, now()))
  returning id into v_id;
  update ide_ledger.issue
     set state = case when state in ('planned', 'ready', 'blocked') then 'in_progress' else state end,
         repair_rung = greatest(repair_rung, p_repair_rung),
         updated_at = now()
   where id = p_issue_id;
  perform ide_ledger._audit('start_run', 'run', p_run_key,
                            jsonb_build_object('issue', p_issue_id, 'attempt', v_attempt,
                                               'executor', p_executor, 'requested_model', p_requested_model));
  return v_id;
end
$$;

-- Closes an attempt. Re-finishing with identical values is a no-op; changing
-- the result of a closed run is rejected.
create or replace function ide_ledger.finish_run(
  p_run_key text,
  p_result text,
  p_self_reported_model text default null,
  p_head_sha text default null,
  p_failure_summary text default null,
  p_cost_usd numeric default null,
  p_ended_at timestamptz default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_run ide_ledger.run%rowtype;
begin
  if p_result = 'running' then
    raise exception 'finish_run needs a terminal result' using errcode = '22023';
  end if;
  select * into v_run from ide_ledger.run where run_key = p_run_key for update;
  if not found then
    raise exception 'unknown run %', p_run_key using errcode = 'P0002';
  end if;
  if v_run.result <> 'running' then
    if v_run.result = p_result then
      return v_run.id;
    end if;
    raise exception 'run % already finished as %', p_run_key, v_run.result using errcode = '55000';
  end if;
  update ide_ledger.run
     set result = p_result,
         self_reported_model = coalesce(p_self_reported_model, self_reported_model),
         head_sha = coalesce(p_head_sha, head_sha),
         failure_summary = p_failure_summary,
         cost_usd = p_cost_usd,
         ended_at = coalesce(p_ended_at, now())
   where id = v_run.id;
  perform ide_ledger._audit('finish_run', 'run', p_run_key,
                            jsonb_build_object('result', p_result, 'head_sha', p_head_sha,
                                               'self_reported_model', p_self_reported_model));
  return v_run.id;
end
$$;

create or replace function ide_ledger.record_decision(
  p_prefix text,
  p_question text,
  p_decision text,
  p_decided_by text,
  p_rationale text default null,
  p_issue_id text default null,
  p_phase_key text default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_id bigint;
begin
  insert into ide_ledger.decision (prefix, issue_id, phase_id, question, decision, rationale, decided_by)
  values (p_prefix, p_issue_id, ide_ledger._phase_id(p_prefix, p_phase_key),
          p_question, p_decision, p_rationale, p_decided_by)
  returning id into v_id;
  perform ide_ledger._audit('record_decision', 'decision', v_id::text,
                            jsonb_build_object('issue', p_issue_id, 'phase', p_phase_key));
  return v_id;
end
$$;

create or replace function ide_ledger.raise_exception(
  p_prefix text,
  p_kind text,
  p_detail text,
  p_issue_id text default null,
  p_run_key text default null
)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_run_id bigint;
  v_id bigint;
begin
  if p_run_key is not null then
    select id into v_run_id from ide_ledger.run where run_key = p_run_key;
    if v_run_id is null then
      raise exception 'unknown run %', p_run_key using errcode = 'P0002';
    end if;
  end if;
  insert into ide_ledger.exception (prefix, issue_id, run_id, kind, detail)
  values (p_prefix, p_issue_id, v_run_id, p_kind, p_detail)
  returning id into v_id;
  perform ide_ledger._audit('raise_exception', 'exception', v_id::text,
                            jsonb_build_object('kind', p_kind, 'issue', p_issue_id, 'run', p_run_key));
  return v_id;
end
$$;

create or replace function ide_ledger.resolve_exception(p_id bigint, p_status text, p_resolution text)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if p_status not in ('resolved', 'dismissed') then
    raise exception 'resolve_exception needs resolved or dismissed' using errcode = '22023';
  end if;
  update ide_ledger.exception
     set status = p_status, resolution = p_resolution, resolved_at = now()
   where id = p_id and status = 'open';
  if not found then
    raise exception 'no open exception %', p_id using errcode = 'P0002';
  end if;
  perform ide_ledger._audit('resolve_exception', 'exception', p_id::text,
                            jsonb_build_object('status', p_status));
end
$$;

-- ---------------------------------------------------------------------------
-- Read RPCs (the restricted role has no table privileges)
-- ---------------------------------------------------------------------------

create or replace function ide_ledger.get_issue(p_issue_id text)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'id', i.id, 'title', i.title, 'state', i.state, 'owner', i.owner_id, 'branch', i.branch,
    'phase', p.phase_key, 'repair_rung', i.repair_rung,
    'depends_on', coalesce((select jsonb_agg(d.depends_on_id order by d.depends_on_id)
                            from ide_ledger.issue_dependency d where d.issue_id = i.id), '[]'::jsonb),
    'runs', coalesce((select jsonb_agg(jsonb_build_object(
                        'run_key', r.run_key, 'attempt', r.attempt, 'executor', r.executor,
                        'requested_model', r.requested_model, 'self_reported_model', r.self_reported_model,
                        'result', r.result, 'head_sha', r.head_sha, 'started_at', r.started_at,
                        'ended_at', r.ended_at) order by r.attempt)
                      from ide_ledger.run r where r.issue_id = i.id), '[]'::jsonb))
  from ide_ledger.issue i
  left join ide_ledger.phase p on p.id = i.phase_id
  where i.id = p_issue_id;
$$;

-- Feeds the one-per-Phase GitHub Issue summary.
create or replace function ide_ledger.phase_summary(p_prefix text, p_phase_key text)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
  select jsonb_build_object(
    'phase', p.phase_key, 'title', p.title, 'state', p.state,
    'github_issue_number', p.github_issue_number,
    'issues', coalesce((select jsonb_agg(jsonb_build_object(
                          'id', i.id, 'title', i.title, 'state', i.state, 'owner', i.owner_id,
                          'branch', i.branch,
                          'runs', (select count(*) from ide_ledger.run r where r.issue_id = i.id))
                          order by i.number)
                        from ide_ledger.issue i where i.phase_id = p.id), '[]'::jsonb))
  from ide_ledger.phase p
  where p.prefix = p_prefix and p.phase_key = p_phase_key;
$$;

-- Watchdog feed: runs still open after p_older_than.
create or replace function ide_ledger.list_stalled_runs(p_prefix text, p_older_than interval)
returns table (run_key text, issue_id text, attempt integer, executor text, started_at timestamptz)
language sql
stable
security definer
set search_path = ''
as $$
  select r.run_key, r.issue_id, r.attempt, r.executor, r.started_at
  from ide_ledger.run r
  join ide_ledger.issue i on i.id = r.issue_id
  where i.prefix = p_prefix and r.result = 'running' and r.started_at < now() - p_older_than
  order by r.started_at;
$$;

-- ---------------------------------------------------------------------------
-- Privileges
-- ---------------------------------------------------------------------------

revoke all on all functions in schema ide_ledger from public;

do $$
declare
  r text;
begin
  foreach r in array array['anon', 'authenticated', 'service_role'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on schema ide_ledger from %I', r);
      execute format('revoke all on all tables in schema ide_ledger from %I', r);
      execute format('revoke all on all sequences in schema ide_ledger from %I', r);
      execute format('revoke all on all functions in schema ide_ledger from %I', r);
    end if;
  end loop;
end
$$;

alter default privileges in schema ide_ledger revoke execute on functions from public;

grant usage on schema ide_ledger to ide_ledger_orchestrator;

grant execute on function
  ide_ledger.register_repo(text, text),
  ide_ledger.upsert_owner(text, text, text),
  ide_ledger.upsert_phase(text, text, text, text, text, integer),
  ide_ledger.create_issue(text, text, text, text, text, text, integer),
  ide_ledger.set_issue_state(text, text, text),
  ide_ledger.set_issue_owner(text, text),
  ide_ledger.set_issue_phase(text, text),
  ide_ledger.add_dependency(text, text),
  ide_ledger.remove_dependency(text, text),
  ide_ledger.start_run(text, text, text, text, text, integer, text, text, timestamptz),
  ide_ledger.finish_run(text, text, text, text, text, numeric, timestamptz),
  ide_ledger.record_decision(text, text, text, text, text, text, text),
  ide_ledger.raise_exception(text, text, text, text, text),
  ide_ledger.resolve_exception(bigint, text, text),
  ide_ledger.get_issue(text),
  ide_ledger.phase_summary(text, text),
  ide_ledger.list_stalled_runs(text, interval)
to ide_ledger_orchestrator;

commit;
