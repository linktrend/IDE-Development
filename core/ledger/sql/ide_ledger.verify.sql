-- Structural and privilege invariants for ide_ledger. Read-only; raises on the
-- first violation. Intended to sit next to the migration in LiNKplatform's
-- supabase/verification/ flow and to run in this repo's local SQL test.

do $$
declare
  v_bad text;
begin
  if not exists (select 1 from pg_namespace where nspname = 'ide_ledger') then
    raise exception 'schema ide_ledger is missing';
  end if;

  if not exists (select 1 from pg_roles where rolname = 'ide_ledger_orchestrator') then
    raise exception 'role ide_ledger_orchestrator is missing';
  end if;

  select string_agg(rolname, ', ') into v_bad
  from pg_roles
  where rolname = 'ide_ledger_orchestrator'
    and (rolsuper or rolcreaterole or rolcreatedb or rolbypassrls or rolreplication);
  if v_bad is not null then
    raise exception 'ide_ledger_orchestrator has elevated attributes';
  end if;

  select string_agg(c.relname, ', ') into v_bad
  from pg_class c join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'ide_ledger' and c.relkind = 'r' and not c.relrowsecurity;
  if v_bad is not null then
    raise exception 'RLS disabled on: %', v_bad;
  end if;

  select string_agg(format('%s:%s', c.relname, r.rolname), ', ') into v_bad
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  cross join (select rolname from pg_roles
              where rolname in ('ide_ledger_orchestrator', 'anon', 'authenticated', 'service_role')
              union all select 'public') r
  where n.nspname = 'ide_ledger' and c.relkind in ('r', 'S', 'v', 'm')
    and (case when r.rolname = 'public'
              then exists (select 1 from aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a
                           where a.grantee = 0)
              else has_table_privilege(r.rolname, c.oid, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
         end);
  if v_bad is not null then
    raise exception 'table privileges leaked: %', v_bad;
  end if;

  select string_agg(p.proname, ', ') into v_bad
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'ide_ledger'
    and (not p.prosecdef
         or not exists (select 1 from unnest(coalesce(p.proconfig, '{}')) cfg
                        where cfg in ('search_path=', 'search_path=""')));
  if v_bad is not null then
    raise exception 'functions must be SECURITY DEFINER with empty search_path: %', v_bad;
  end if;

  select string_agg(p.proname, ', ') into v_bad
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'ide_ledger'
    and exists (select 1 from aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a where a.grantee = 0);
  if v_bad is not null then
    raise exception 'EXECUTE granted to PUBLIC on: %', v_bad;
  end if;

  select string_agg(p.proname, ', ') into v_bad
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'ide_ledger' and p.proname like '\_%'
    and has_function_privilege('ide_ledger_orchestrator', p.oid, 'EXECUTE');
  if v_bad is not null then
    raise exception 'internal helpers executable by ide_ledger_orchestrator: %', v_bad;
  end if;

  select string_agg(p.proname, ', ') into v_bad
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'ide_ledger' and p.proname not like '\_%'
    and not has_function_privilege('ide_ledger_orchestrator', p.oid, 'EXECUTE');
  if v_bad is not null then
    raise exception 'RPCs not executable by ide_ledger_orchestrator: %', v_bad;
  end if;

  select string_agg(format('%s:%s', p.proname, r.rolname), ', ') into v_bad
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  cross join (select rolname from pg_roles where rolname in ('anon', 'authenticated')) r
  where n.nspname = 'ide_ledger' and has_function_privilege(r.rolname, p.oid, 'EXECUTE');
  if v_bad is not null then
    raise exception 'EXECUTE reachable by API roles: %', v_bad;
  end if;
end
$$;

select 'ide_ledger verify: ok' as result;
