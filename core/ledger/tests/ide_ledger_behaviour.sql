-- Behaviour test for ide_ledger, run as the restricted role against a
-- throwaway database. Used by scripts/ledger/test-ide-ledger-sql.sh.

\set ON_ERROR_STOP on
set role ide_ledger_orchestrator;

do $$
declare
  v_id text;
  v_run bigint;
  v_exc bigint;
  v_json jsonb;
  v_denied boolean;
begin
  perform ide_ledger.register_repo('IDE', 'linktrend/IDE-Development');
  perform ide_ledger.register_repo('IDE', 'linktrend/IDE-Development');
  perform ide_ledger.upsert_owner('project:ide-development', 'project', 'IDE Development Project');
  perform ide_ledger.upsert_phase('IDE', '0.5', 'Ledger design', 'active', 'project:ide-development', 12);

  v_id := ide_ledger.create_issue('IDE', 'Ledger schema', 'ledger-schema', 'project:ide-development', '0.5', 'ready', 4);
  assert v_id = 'IDE-4', 'explicit number keeps pilot ID';
  v_id := ide_ledger.create_issue('IDE', 'Next', 'next-thing', 'project:ide-development', '0.5');
  assert v_id = 'IDE-5', format('allocation continues after explicit number, got %s', v_id);

  perform ide_ledger.add_dependency('IDE-5', 'IDE-4');
  begin
    perform ide_ledger.add_dependency('IDE-4', 'IDE-5');
    raise exception 'cycle was accepted';
  exception when check_violation then null;
  end;

  v_run := ide_ledger.start_run('run-ide4-0001', 'IDE-4', 'cursor-002', 'grok-4.7', 'medium', 0,
                                'issue/IDE-4-ledger-schema', 'bc-test');
  assert v_run = ide_ledger.start_run('run-ide4-0001', 'IDE-4', 'cursor-002', 'grok-4.7'),
         'start_run is idempotent on run_key';
  perform ide_ledger.finish_run('run-ide4-0001', 'failure', 'grok-4.7 (self-report)', null, 'tests red', 0.12);
  perform ide_ledger.finish_run('run-ide4-0001', 'failure');
  begin
    perform ide_ledger.finish_run('run-ide4-0001', 'success');
    raise exception 'closed run result was changed';
  exception when object_not_in_prerequisite_state then null;
  end;

  perform ide_ledger.start_run('run-ide4-0002', 'IDE-4', 'codex-cli', 'gpt-6-sol', 'medium', 1);
  perform ide_ledger.finish_run('run-ide4-0002', 'success', 'gpt-6-sol', 'abc1234def');

  v_json := ide_ledger.get_issue('IDE-4');
  assert v_json->>'state' = 'in_progress', 'start_run moves issue to in_progress';
  assert v_json->>'branch' = 'issue/IDE-4-ledger-schema', 'branch is derived from ID and slug';
  assert (v_json->>'repair_rung')::int = 1, 'repair rung tracks highest attempt rung';
  assert jsonb_array_length(v_json->'runs') = 2, 'two attempts recorded';
  assert v_json->'runs'->1->>'attempt' = '2', 'attempt numbers increment';
  assert v_json->'depends_on' = '[]'::jsonb, 'IDE-4 has no dependencies';

  perform ide_ledger.set_issue_state('IDE-4', 'done', 'merged');
  perform ide_ledger.set_issue_owner('IDE-5', 'project:ide-development');
  perform ide_ledger.record_decision('IDE', 'Ledger location?', 'Platform Supabase, schema ide_ledger',
                                     'project:ide-development', 'Q22 = A', null, '0.5');

  perform ide_ledger.start_run('run-ide5-0001', 'IDE-5', 'codex-cli', 'gpt-6-luna', 'high', 0, null, null,
                               now() - interval '3 hours');
  assert (select count(*) from ide_ledger.list_stalled_runs('IDE', interval '2 hours')) = 1, 'stalled run listed';
  v_exc := ide_ledger.raise_exception('IDE', 'stalled_run', 'no push for 3h', 'IDE-5', 'run-ide5-0001');
  perform ide_ledger.resolve_exception(v_exc, 'resolved', 'restarted');

  v_json := ide_ledger.phase_summary('IDE', '0.5');
  assert jsonb_array_length(v_json->'issues') = 2, 'phase summary lists both issues';
  assert (v_json->>'github_issue_number')::int = 12, 'phase links its GitHub Issue';

  begin
    perform ide_ledger.create_issue('IDE', 'Bad', 'Bad Slug', 'project:ide-development');
    raise exception 'invalid slug was accepted';
  exception when check_violation then null;
  end;

  v_denied := false;
  begin
    perform count(*) from ide_ledger.issue;
  exception when insufficient_privilege then v_denied := true;
  end;
  assert v_denied, 'restricted role must not SELECT tables';

  v_denied := false;
  begin
    insert into ide_ledger.owner (id, kind, display_name) values ('x-owner', 'external', 'x');
  exception when insufficient_privilege then v_denied := true;
  end;
  assert v_denied, 'restricted role must not INSERT tables';

  v_denied := false;
  begin
    perform ide_ledger._audit('forged', 'issue', 'IDE-4', '{}');
  exception when insufficient_privilege then v_denied := true;
  end;
  assert v_denied, 'restricted role must not call internal helpers';

  v_denied := false;
  begin
    create table ide_ledger.sneaky (id int);
  exception when insufficient_privilege then v_denied := true;
  end;
  assert v_denied, 'restricted role must not create objects in the schema';
end
$$;

reset role;

do $$
begin
  assert (select count(*) from ide_ledger.audit_log where actor = session_user) > 0, 'audit rows written';
  assert (select count(*) from ide_ledger.audit_log where action = 'forged') = 0, 'no forged audit rows';
end
$$;

select 'ide_ledger behaviour: ok' as result;
