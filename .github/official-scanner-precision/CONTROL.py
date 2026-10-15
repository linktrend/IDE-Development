"""Hosted-only official scanner focused proof; no consumer scan or rollout."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from types import MappingProxyType

REPO="linktrend/IDE-Development"
SOURCE="5a73a1f40c1b9c41f778a2737bcb565998027b4d"
TREE="4c58b5efbb53f339c078713c2ce5ed9c773ab7ae"
BASE="a78c63762bca53c17b283ca70c4f65e0de232e4b"
BASE_TREE="20f99eb03a4d0f7bef4a74627db694c063041213"
REF="refs/heads/proof/official-scanner-precision-repair1"
HERE=".github/official-scanner-precision/CONTROL.py"
REPORTER=".github/official-scanner-precision/REPORTER.py"
REPORTER_SHA="e63ae0f9588714414522c0d50d3c5a7ad0e58f2f0628de468acc7b5a6a183449"
WORKFLOW=".github/workflows/ide-development-cross-platform.yml"
FIXTURE=".github/linktrend-secret-scan-fixtures.json"
MANIFEST="core/managed-core/MANIFEST.json"
ALLOWED={FIXTURE,MANIFEST}
SCANNER="scripts/gitops/secret_scan.py"
TEST_FILE="scripts/tests/test_fixture_aware_secret_scan.py"
CHANGED={SCANNER:"12047388c88950b018116585940d1dfbdbb8236a",TEST_FILE:"0db6b9aae60674df2183338444682e6fdfb76f92"}
SOURCE_HASHES={SCANNER:"dd34780b05890a5762fd8dc18cde7a3c82aa02b598670a17db03dc7b07c00109",TEST_FILE:"60312dff41f52e0939021a6d1806a20e42cfecef84b975a83705b9c426ffb905"}
BASE_BLOBS={SCANNER:"eaba7aa943cbd766f04026c51283116ea37997c7",TEST_FILE:"a4630ed27e23d54803e7c93b0c17e0540a0dfac7",
 FIXTURE:"e071ba8d2e91c7e1fd0b3f6db9c92d5d4fa11188",MANIFEST:"5246f466487134830eef18ea33001eb60318d012",
 "scripts/gitops/generated_output_closure.py":"75c14c2cb144a1322db26283d903a8a60d8b19d1",
 "scripts/gitops/secret_scan_migrate.py":"01cfee6f53b07284560c2c9f755c0d3e91b4d4a2",
 "scripts/gitops/mutation_guard.py":"aabf4c61aab14d57814ed13e3bddf763c141c0d6",
 "scripts/ide_development/build_manifest.py":"f548e5c2c3bd3d2926d49c046cc71810331091e7",
 "scripts/ide_development/constants.py":"c1efdc4833494c6529d8d3ec75ec67222e1f5890",
 "scripts/ide_development/hashing.py":"40f7b2eb79e39abccb597e14f5808d5d0176e0e2",
 "scripts/ide_development/__init__.py":"eff632a0154b216d9c07f49c18d581142d451e28",
 "core/github/managed-runtime/MANIFEST.json":"4506ae2ddcabd66dd57554a0a0c6da244d9e35fe",
 "core/managed-core/config/generated-output-closure.json":"f51a8c2953fd6a2b176dbb5599b928a0f546eea7",
 "core/managed-core/schemas/change-scoped-secret-scan.schema.json":"e2c1ff315a873dad9d60be443f4a521d81924ec6",
 "core/managed-core/schemas/secret-scan-fixtures.schema.json":"a0dc5116347ed41120b2cfe632ff336298cf592c",
 "core/managed-core/schemas/secret-scan-result.schema.json":"2c4a03fd33518788fe4072f87da2c25a362645c1",
 "core/managed-core/INDEX.yaml":"b957ff848e4d1c5fcfaf736b405a6babafdd7f0c",
 ".github/linktrend-delivery-mode.json":"4759ebf1118843fd4ee31425d2831c764fabe494",
 "core/managed-core/config/delivery.json":"f982be206d16e1debc37458153a326a665572258",
 "docs/contracts/DELIVERY-MODES.md":"cd8ef49cd5d210289ec501aec7000de421b1705d",
 "docs/contracts/SECRET-SCAN-FIXTURES.md":"ecdaf1c048c5ff4a6adabc1bcafa170d0a554a47",
 "docs/contracts/STREAMLINED-DELIVERY.md":"77b156624281e75a17e2bc280651f77b6a70ff5d"}
EXPECTED=["CodeExpressionTests.test_callable_keyword_arguments_are_not_credentials","CodeExpressionTests.test_bash_parameter_defaults_exclude_operator_from_secret_value","CodeExpressionTests.test_non_parameter_value_keeps_leading_dash","ChangedPathStatusTests.test_copy_status_includes_source_and_destination","ChangedPathStatusTests.test_rename_status_includes_source_and_destination","ChangedPathStatusTests.test_malformed_copy_status_fails_closed","ChangedPathStatusTests.test_delete_and_invalid_copy_paths_remain_fail_closed","ChangedPathStatusTests.test_declared_migration_deletion_is_included","ChangedPathStatusTests.test_undeclared_migration_deletion_fails_closed","PackagingContractTests.test_schemas_index_manifest_and_fast_cover_scanner","PackagingContractTests.test_checked_in_fixture_declaration_binds_current_candidate_tree","PackagingContractTests.test_doctrine_and_installer_docs_name_fixture_contract","AcU1001SyntheticLiteralTests.test_declared_synthetic_assignment_passes_without_syntax_evasion","AcU1004ExactScopeTests.test_same_bytes_in_other_file_line_field_or_production_path_fail","AcU1005FailClosedTests.test_one_byte_change_fails_closed","AcU1005FailClosedTests.test_stale_digest_fails_closed","AcU1005FailClosedTests.test_renamed_file_fails_closed","AcU1005FailClosedTests.test_duplicated_value_fails_closed","AcU1005FailClosedTests.test_duplicate_fixture_ids_cannot_hide_stale_declaration","AcU1005FailClosedTests.test_unknown_rule_fails_closed","AcU1005FailClosedTests.test_undeclared_fixture_fails_closed","AcU1006RealisticFormatsTests.test_realistic_formats_cannot_be_approved","AcU1007AggregationTests.test_one_run_reports_all_findings_and_fixture_errors","AcU1008BindingTests.test_tree_or_policy_change_invalidates_until_refresh","AcU1008BindingTests.test_changed_package_source_refreshes_binding_without_oscillation","AcU1002NoBlindSpotTests.test_production_path_and_test_directory_are_both_scanned","AcU1002NoBlindSpotTests.test_missing_or_malformed_declaration_fails_closed","AcU1009RepositoryScannersTests.test_repository_owned_scanner_failure_remains_blocking","AcU1009RepositoryScannersTests.test_fixture_declaration_cannot_suppress_repository_scanner","AcU1003MigrationHelperTests.test_migration_identifies_candidates_and_never_writes_approval","CliAggregationTests.test_cli_writes_aggregate_result_and_nonzero_on_findings","AdversarialRepairTests.test_directory_symlink_and_option_like_path_use_index_identities","AdversarialRepairTests.test_suffix_named_text_and_utf16_are_scanned","AdversarialRepairTests.test_declaration_bytes_and_notes_cannot_hide_credentials","AdversarialRepairTests.test_unquoted_env_yaml_short_and_escaped_secrets","AdversarialRepairTests.test_quoted_member_and_call_references_are_not_assignment_findings","AdversarialRepairTests.test_six_credential_formats_remain_blocking","AdversarialRepairTests.test_huge_input_and_scanner_timeout_are_typed_results","AdversarialRepairTests.test_schema_extras_and_typed_failures_match_result_schema","AdversarialRepairTests.test_undecodable_nul_content_fails_closed","AdversarialRepairTests.test_binary_and_high_control_content_is_typed_nonblocking_skip","AdversarialRepairTests.test_bound_bytes_must_match_detected_value","AdversarialRepairTests.test_matching_bytes_still_approve_synthetic_only","ChangeScopedEvidenceTests.test_changed_credential_blocks_and_unchanged_finding_is_inherited","ChangeScopedEvidenceTests.test_unchanged_pre_existing_credential_is_permitted","ChangeScopedEvidenceTests.test_unchanged_baseline_fixture_declaration_is_inherited","ChangeScopedEvidenceTests.test_changed_source_cannot_use_inherited_fixture_row","ChangeScopedEvidenceTests.test_ten_thousand_approved_inherited_findings_do_not_force_full_rescan","ChangeScopedEvidenceTests.test_identity_config_and_managed_path_drift_fail_closed","ChangeScopedEvidenceTests.test_expected_managed_edit_is_scanned_but_unrelated_dirty_state_blocks","ChangeScopedEvidenceTests.test_installer_manifest_destinations_are_allowed_but_unrelated_dirty_is_not","ChangeScopedEvidenceTests.test_untracked_installer_manifest_destination_is_allowed_but_unrelated_is_not","ChangeScopedEvidenceTests.test_generated_manifest_and_declared_migration_cleanup_are_allowed_but_unrelated_paths_block","ChangeScopedEvidenceTests.test_absent_declared_migration_path_is_allowed_but_absent_unrelated_path_blocks","ChangeScopedEvidenceTests.test_rename_is_scope_ambiguity_not_an_ignore","ChangeScopedEvidenceTests.test_path_scoped_result_emits_real_head_identity","ChangeScopedEvidenceTests.test_full_scan_omits_candidate_commit_identity","ChangeScopedEvidenceTests.test_extracted_managed_root_uses_packaged_policy_paths","TypedPublicCredentialReferencePrecisionTests.test_public_marker_predicates_are_not_private_key_material","TypedPublicCredentialReferencePrecisionTests.test_short_invalid_bytes_envelope_is_format_data","TypedPublicCredentialReferencePrecisionTests.test_bare_header_and_stored_marker_remain_blocking","TypedPublicCredentialReferencePrecisionTests.test_real_and_ambiguous_envelopes_remain_blocking","TypedPublicCredentialReferencePrecisionTests.test_valid_private_key_der_body_remains_blocking","TypedPublicCredentialReferencePrecisionTests.test_public_marker_does_not_hide_other_markers_or_secrets","TypedPublicCredentialReferencePrecisionTests.test_complete_encrypted_binding_is_a_reference","TypedPublicCredentialReferencePrecisionTests.test_malformed_binding_does_not_mask_nested_assignment","TypedPublicCredentialReferencePrecisionTests.test_runtime_private_key_requires_exact_manager_path","TypedPublicCredentialReferencePrecisionTests.test_typed_references_preserve_all_other_credential_detectors","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_accepts_public_contexts_without_new_fixtures","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_keeps_real_material_and_entropy_blocking","TypedPublicCredentialReferencePrecisionTests.test_generic_entropy_inside_valid_manager_reference_blocks","TypedPublicCredentialReferencePrecisionTests.test_generic_entropy_inside_valid_encrypted_binding_blocks","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_does_not_accept_opaque_reference_components"]
NEW={k for k in EXPECTED if k.startswith("TypedPublicCredentialReferencePrecisionTests.")}
ROOT=Path(os.environ["GITHUB_WORKSPACE"]).resolve()
CONTROL=ROOT/"control"
CANDIDATE=ROOT/"candidate"
TRUSTED=ROOT/"trusted"
PRIVATE=Path(os.environ["RUNNER_TEMP"])/"official-scanner-focused-private"
SAFE=PRIVATE/"safe"
SEALED=Path(os.environ["RUNNER_TEMP"])/"official-scanner-focused-sealed"
VENV=PRIVATE/"venv"
PHASES={"startup","source_identity","dependencies","manifest_generation","manifest_verification","fixture_generation","focused_tests","post_identity","complete"}
CODES={"not_started","source_identity_failed","control_identity_failed","dependency_failed","manifest_generation_failed","manifest_drift",
 "fixture_generation_failed","fixture_drift","focused_tests_failed","focused_result_invalid","source_changed","capture_timeout","capture_oversized","artifact_invalid","passed","internal_failure"}
ERROR_TYPES={"AssertionError","ValueError","TypeError","KeyError","IndexError","RuntimeError","OSError","FileNotFoundError","PermissionError","TimeoutError","TimeoutExpired","CalledProcessError","ImportError","ModuleNotFoundError","SyntaxError","other"}
STATES={"started","passed","failed","error","skipped","expected_failure","unexpected_success"}
_ENTRY_CACHE={}
class Stop(Exception): pass
def need(ok,code="source_identity_failed"):
 if not ok: raise Stop(code)
def encoded(value): return (json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
def regular(root,rel):
 need(type(rel) is str and not rel.startswith("/") and all(p not in {"",".",".."} for p in rel.split("/")))
 path=root;need(not path.is_symlink())
 for p in rel.split("/"): path/=p;need(not path.is_symlink())
 need(stat.S_ISREG(path.lstat().st_mode));return path
def safe_path(path):
 return type(path) is str and 0<len(path)<=384 and re.fullmatch("[A-Za-z0-9._/-]+",path) is not None and not path.startswith("/") and all(p not in {"",".",".."} for p in path.split("/"))
def git(repo,*args):
 p=subprocess.run(["git","-c","core.fsmonitor=false",*args],cwd=repo,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15,check=False,
  env={"PATH":os.environ["PATH"],"GIT_CONFIG_GLOBAL":"/dev/null","GIT_CONFIG_NOSYSTEM":"1","GIT_TERMINAL_PROMPT":"0"})
 need(p.returncode==0 and len(p.stdout)<=16*1024*1024);return p.stdout
def text(repo,*args): return git(repo,*args).decode("utf-8","strict").strip()
def emit(**values):
 with open(os.environ["GITHUB_OUTPUT"],"a") as f:
  for k,v in values.items(): f.write(k+"="+v+"\n")
def digest(path): return hashlib.sha256(regular(path.parent,path.name).read_bytes()).hexdigest()
def window(margin=0):
 raw=os.environ["DEADLINE_UTC"];need(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",raw))
 end=datetime.datetime.strptime(raw,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
 need(end<=datetime.datetime(2026,10,16,tzinfo=datetime.timezone.utc) and datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(minutes=margin)<end)
def control_identity():
 need(os.environ["GITHUB_REPOSITORY"]==REPO and os.environ["GITHUB_EVENT_NAME"]=="workflow_dispatch"
  and os.environ["GITHUB_REF"]==REF and os.environ["GITHUB_RUN_ATTEMPT"]=="1","control_identity_failed")
 sha,tree=os.environ["CONTROL_SHA"],os.environ["CONTROL_TREE"]
 need(re.fullmatch("[0-9a-f]{40}",sha) and re.fullmatch("[0-9a-f]{40}",tree)
  and sha==os.environ["GITHUB_SHA"]==os.environ["GITHUB_WORKFLOW_SHA"],"control_identity_failed")
 need(text(CONTROL,"rev-parse","HEAD")==sha and text(CONTROL,"rev-parse","HEAD^{tree}")==tree
  and text(CONTROL,"show","-s","--format=%P","HEAD")==BASE
  and text(CONTROL,"rev-parse",BASE+"^{tree}")==BASE_TREE,"control_identity_failed")
 for rel in (HERE,REPORTER,WORKFLOW): need(regular(CONTROL,rel).read_bytes()==git(CONTROL,"show",sha+":"+rel),"control_identity_failed")
 need(digest(regular(CONTROL,REPORTER))==REPORTER_SHA,"control_identity_failed")
def entries(tree):
 if tree not in _ENTRY_CACHE:
  result={}
  for row in git(CANDIDATE,"ls-tree","-r","-z",tree).split(b"\0"):
   if row:
    meta,raw=row.split(b"\t",1);mode,kind,oid=meta.decode().split();rel=raw.decode("utf-8","strict")
    need(kind=="blob" and mode in {"100644","100755","120000"} and not rel.startswith("/") and all(p not in {"",".",".."} for p in rel.split("/")))
    result[rel]=(mode,oid)
  _ENTRY_CACHE[tree]=MappingProxyType(result)
 return _ENTRY_CACHE[tree]
def physical(tree):
 expected=entries(tree);need(not CANDIDATE.is_symlink())
 for rel,(mode,oid) in expected.items():
  path=CANDIDATE/rel
  if mode=="120000":
   need(path.is_symlink(),"source_changed");raw=os.fsencode(os.readlink(path))
   actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
  else:
   path=regular(CANDIDATE,rel);size=path.stat().st_size;h=hashlib.sha1(b"blob "+str(size).encode()+b"\0")
   with path.open("rb") as f:
    for chunk in iter(lambda:f.read(262144),b""): h.update(chunk)
   actual=h.hexdigest();need(bool(path.stat().st_mode&0o111)==(mode=="100755"),"source_changed")
  need(actual==oid,"source_changed")
 seen=set()
 for base,dirs,files in os.walk(CANDIDATE,followlinks=False):
  current=Path(base)
  if current==CANDIDATE:
   if ".git" in dirs: dirs.remove(".git")
   if ".git" in files: files.remove(".git")
  for item in list(dirs):
   path=current/item
   if path.is_symlink():
    rel=path.relative_to(CANDIDATE).as_posix();need(rel in expected and expected[rel][0]=="120000","source_changed");seen.add(rel);dirs.remove(item)
  for item in files:
   rel=(current/item).relative_to(CANDIDATE).as_posix();need(rel in expected,"source_changed");seen.add(rel)
 need(seen==set(expected),"source_changed")
def source_identity(raw=False):
 need(text(CANDIDATE,"rev-parse","HEAD")==SOURCE and text(CANDIDATE,"rev-parse","HEAD^{tree}")==TREE
  and text(CANDIDATE,"show","-s","--format=%P","HEAD")==BASE and text(CANDIDATE,"rev-parse",BASE+"^{tree}")==BASE_TREE)
 need(set(text(CANDIDATE,"diff","--no-renames","--name-only",BASE,SOURCE).splitlines())==set(CHANGED))
 for rel,oid in CHANGED.items():
  need(text(CANDIDATE,"ls-tree",SOURCE,"--",rel)=="100644 blob "+oid+"\t"+rel and digest(regular(CANDIDATE,rel))==SOURCE_HASHES[rel])
 for rel,oid in BASE_BLOBS.items():
  need(text(CANDIDATE,"ls-tree",BASE,"--",rel)=="100644 blob "+oid+"\t"+rel)
  if rel not in CHANGED and rel not in ALLOWED: need(text(CANDIDATE,"ls-tree",SOURCE,"--",rel)=="100644 blob "+oid+"\t"+rel)
 if raw:
  need(text(CANDIDATE,"status","--porcelain=v1","--untracked-files=all","--ignored")=="")
  need(text(CANDIDATE,"write-tree")==TREE);physical(TREE)
def environment():
 return {"PATH":str(VENV/"bin")+":"+os.environ["PATH"],"HOME":str(PRIVATE/"home"),"TMPDIR":str(PRIVATE/"tmp"),"CI":"true","NO_COLOR":"1",
  "PYTHONDONTWRITEBYTECODE":"1","PYTHONNOUSERSITE":"1","GIT_CONFIG_GLOBAL":"/dev/null","GIT_CONFIG_NOSYSTEM":"1","GIT_TERMINAL_PROMPT":"0"}
def trusted_identity():
 need(text(TRUSTED,"rev-parse","HEAD")==BASE and text(TRUSTED,"rev-parse","HEAD^{tree}")==BASE_TREE)
 for rel in (SCANNER,"scripts/gitops/generated_output_closure.py","scripts/gitops/mutation_guard.py"):
  need(text(TRUSTED,"ls-tree",BASE,"--",rel)=="100644 blob "+BASE_BLOBS[rel]+"\t"+rel
   and regular(TRUSTED,rel).read_bytes()==git(TRUSTED,"show",BASE+":"+rel))
def capture(argv,label,seconds,extra=None):
 window();env=environment()
 if extra: env.update(extra)
 start=time.monotonic();status=None;size=0
 with (PRIVATE/(label+".stdout")).open("wb") as out,(PRIVATE/(label+".stderr")).open("wb") as err:
  p=subprocess.Popen(argv,cwd=CANDIDATE,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True)
  sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ,out);sel.register(p.stderr,selectors.EVENT_READ,err)
  try:
   while sel.get_map():
    if time.monotonic()-start>seconds: status="capture_timeout";break
    for key,event in sel.select(.05):
     data=os.read(key.fd,65536)
     if not data: sel.unregister(key.fileobj);continue
     if size+len(data)>4*1024*1024: status="capture_oversized";break
     key.data.write(data);size+=len(data)
    if status: break
   if status is None:
    try: p.wait(timeout=max(.1,seconds-(time.monotonic()-start)))
    except subprocess.TimeoutExpired: status="capture_timeout"
  finally:
   try: os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError: pass
   code=p.wait(timeout=5);sel.close();p.stdout.close();p.stderr.close()
 return status,code
def command(argv,label,seconds,extra=None):
 status,code=capture(argv,label,seconds,extra)
 if status: raise Stop(status)
 return code
def baseline_fixture(): return json.loads(git(CANDIDATE,"show",BASE+":"+FIXTURE))
def stable_fixture(value):
 need(type(value) is dict and set(value)=={"schemaVersion","kind","scannerPolicyVersion","candidateTree","fixtures"}
  and type(value["schemaVersion"]) is int and value["schemaVersion"]==1 and value["kind"]=="secret-scan-fixtures"
  and value["scannerPolicyVersion"]=="secret-scan-policy/v1" and type(value["candidateTree"]) is str and re.fullmatch("[0-9a-f]{40}",value["candidateTree"])
  and type(value["fixtures"]) is list and len(value["fixtures"])==42,"fixture_drift")
 rows=[]
 for row in value["fixtures"]:
  need(type(row) is dict and type(row.get("line")) is int and 0<row["line"]<=10000000,"fixture_drift")
  rows.append({k:v for k,v in row.items() if k!="line"})
 return {k:v for k,v in value.items() if k not in {"candidateTree","fixtures"}},rows
def manifest_guard():
 before=json.loads(git(CANDIDATE,"show",SOURCE+":"+MANIFEST));after=json.loads(regular(CANDIDATE,MANIFEST).read_bytes())
 need(type(before) is dict and type(after) is dict and set(before)==set(after) and type(before.get("files")) is list and type(after.get("files")) is list,"manifest_drift")
 need({k:v for k,v in before.items() if k!="files"}=={k:v for k,v in after.items() if k!="files"} and len(before["files"])==len(after["files"]),"manifest_drift")
 updates=set()
 for old,new in zip(before["files"],after["files"]):
  need(type(old) is dict and type(new) is dict,"manifest_drift")
  rel=old.get("source")
  if rel in SOURCE_HASHES:
   need({k:v for k,v in old.items() if k!="sourceHash"}=={k:v for k,v in new.items() if k!="sourceHash"}
    and new.get("sourceHash")=="sha256:"+SOURCE_HASHES[rel],"manifest_drift");updates.add(rel)
  else: need(old==new,"manifest_drift")
 need(updates==set(CHANGED),"manifest_drift")
def derivative_guard():
 source_identity();need(text(CANDIDATE,"diff","--name-only")=="","source_changed")
 changes=set(text(CANDIDATE,"diff","--cached","--no-renames","--name-only",SOURCE).splitlines());need(changes==ALLOWED,"source_changed")
 need(not text(CANDIDATE,"ls-files","--others","--exclude-standard") and not text(CANDIDATE,"ls-files","--others","--ignored","--exclude-standard"),"source_changed")
 manifest_guard();current=json.loads(regular(CANDIDATE,FIXTURE).read_bytes())
 need(stable_fixture(current)==stable_fixture(baseline_fixture()),"fixture_drift")
 tree=text(CANDIDATE,"write-tree");physical(tree);return tree
def coordinate(path,line,tree):
 if not safe_path(path) or type(line) is not int or not 0<line<=10000000: return False
 row=entries(tree).get(path)
 return row is not None and row[0] in {"100644","100755"} and line<=len(regular(CANDIDATE,path).read_bytes().splitlines())
def bounded_int(n,maximum=1000000): return type(n) is int and 0<=n<=maximum
def validate_results(value,tree):
 keys={"schemaVersion","kind","module","testFile","testsRun","counts","nativeFailureEvents","nativeErrorEvents","nativeSkipEvents",
  "nativeExpectedFailures","nativeUnexpectedSuccesses","subtestFailureEvents","namedNewCount","namedNewPassed","passed","records",
  "startupError","rawAssertionsIncluded","rawMessagesIncluded","rawValuesIncluded"}
 need(type(value) is dict and set(value)==keys and type(value["schemaVersion"]) is int and value["schemaVersion"]==1
  and value["kind"]=="official-scanner-native-unittest-results" and value["module"]=="scripts.tests.test_fixture_aware_secret_scan"
  and value["testFile"]==TEST_FILE,"focused_result_invalid")
 for key in ("testsRun","nativeFailureEvents","nativeErrorEvents","nativeSkipEvents","nativeExpectedFailures","nativeUnexpectedSuccesses","subtestFailureEvents","namedNewCount","namedNewPassed"):
  need(bounded_int(value[key]),"focused_result_invalid")
 need(value["testsRun"]<=73 and value["namedNewCount"]==15 and value["namedNewPassed"]<=15
  and type(value["passed"]) is bool and all(value[k] is False for k in ("rawAssertionsIncluded","rawMessagesIncluded","rawValuesIncluded")),"focused_result_invalid")
 need(type(value["records"]) is list and len(value["records"])<=73 and type(value["counts"]) is dict and set(value["counts"])==STATES
  and all(bounded_int(n,73) for n in value["counts"].values()),"focused_result_invalid")
 seen=set();counts={k:0 for k in STATES};new_pass=0
 for row in value["records"]:
  need(type(row) is dict and set(row)=={"test","outcome","errorType","locations","omittedLocations","errorEvents"}
   and type(row["test"]) is str and row["test"] in EXPECTED and row["test"] not in seen and type(row["outcome"]) is str and row["outcome"] in STATES
   and (row["errorType"] is None or type(row["errorType"]) is str and row["errorType"] in ERROR_TYPES)
   and bounded_int(row["omittedLocations"]) and bounded_int(row["errorEvents"]) and type(row["locations"]) is list and len(row["locations"])<=4,"focused_result_invalid")
  seen.add(row["test"]);counts[row["outcome"]]+=1;new_pass+=int(row["test"] in NEW and row["outcome"]=="passed")
  for loc in row["locations"]:
   need(type(loc) is dict and set(loc)=={"path","line"} and coordinate(loc["path"],loc["line"],tree),"focused_result_invalid")
 need(counts==value["counts"] and sum(counts.values())==value["testsRun"] and new_pass==value["namedNewPassed"],"focused_result_invalid")
 if value["startupError"] is not None:
  startup=value["startupError"]
  need(type(startup) is dict and set(startup)=={"errorType","locations","omittedLocations"}
   and type(startup["errorType"]) is str and startup["errorType"] in ERROR_TYPES
   and bounded_int(startup["omittedLocations"]) and type(startup["locations"]) is list and len(startup["locations"])<=4
   and value["testsRun"]==0 and value["records"]==[],"focused_result_invalid")
  for loc in startup["locations"]:
   need(type(loc) is dict and set(loc)=={"path","line"} and coordinate(loc["path"],loc["line"],tree),"focused_result_invalid")
 positive=(value["startupError"] is None and seen==set(EXPECTED) and counts["passed"]==73 and value["testsRun"]==73 and new_pass==15
  and all(value[k]==0 for k in ("nativeFailureEvents","nativeErrorEvents","nativeSkipEvents","nativeExpectedFailures","nativeUnexpectedSuccesses","subtestFailureEvents")))
 need(value["passed"]==positive,"focused_result_invalid");return positive
def fixed_state():
 return {"schemaVersion":1,"kind":"official-scanner-focused-source-proof","repository":REPO,"sourceSha":SOURCE,"sourceTree":TREE,
  "sourceParent":BASE,"sourceParentTree":BASE_TREE,"controlSha":os.environ["CONTROL_SHA"],"controlTree":os.environ["CONTROL_TREE"],
  "controlRef":REF,"runId":os.environ["GITHUB_RUN_ID"],"attempt":1,"phase":"startup","code":"not_started","passed":False,
  "python":"3.11","jsonschema":"4.26.0","dependencyResolution":"existing_ci_direct_pin_transitives_not_locked",
  "dependencyExit":None,"manifestExit":None,"manifestVerifyExit":None,"fixtureExit":None,"testExit":None,
  "preparedIndexTree":None,"candidateContentTree":None,"generatedOutputs":None,"sourcePreserved":False,"approvalCount":42,"newApprovals":0,"testsRun":0,"newTestsPassed":0,"testResultsConfirmed":False,
  "nativeSkipped":0,"nativeFailures":0,"nativeErrors":0,"rawLogsIncluded":False,"rawValuesIncluded":False,
  "consumerScan":False,"consumerInstall":False,"installerQualification":False,"fullReceipt":False,"canonicalCheckpoint":False,"rollout":False}
def write(path,value,limit):
 data=encoded(value);need(len(data)<=limit and not path.is_symlink(),"artifact_invalid");path.write_bytes(data);path.chmod(0o600)
def persist(state,tests,patch):
 write(SAFE/"identity.json",state,16*1024)
 need(len(patch)<=384*1024 and not (SAFE/"generated.patch").is_symlink(),"artifact_invalid")
 (SAFE/"generated.patch").write_bytes(patch);(SAFE/"generated.patch").chmod(0o600)
 if tests is not None: write(SAFE/"tests.json",tests,96*1024)
 emit(identity_sha=digest(SAFE/"identity.json"),patch_sha=digest(SAFE/"generated.patch"),
  tests_sha=digest(SAFE/"tests.json") if tests is not None else "none",passed="true" if state["passed"] else "false")
def run():
 window();control_identity()
 PRIVATE.mkdir(mode=0o700);SAFE.mkdir(mode=0o700)
 for name in ("home","tmp"): (PRIVATE/name).mkdir(mode=0o700)
 state=fixed_state();tests=None;patch=b""
 try:
  state["phase"]="source_identity";persist(state,None,patch);source_identity(raw=True)
  need(sys.version_info[:2]==(3,11),"dependency_failed")
  trusted_identity()
  need(stable_fixture(json.loads(regular(CANDIDATE,FIXTURE).read_bytes()))==stable_fixture(baseline_fixture()),"fixture_drift")
  state["phase"]="dependencies";persist(state,None,patch)
  need(command([sys.executable,"-m","venv",str(VENV)],"venv",10)==0,"dependency_failed")
  python=str(VENV/"bin/python")
  state["dependencyExit"]=command([python,"-m","pip","--isolated","install","--disable-pip-version-check","--no-input","--index-url","https://pypi.org/simple","jsonschema==4.26.0"],"dependencies",45)
  need(state["dependencyExit"]==0,"dependency_failed")
  control_identity();source_identity(raw=True)
  state["phase"]="manifest_generation";persist(state,None,patch)
  state["manifestExit"]=command([python,"-B","scripts/ide_development/build_manifest.py","--write"],"manifest",20)
  need(state["manifestExit"]==0,"manifest_generation_failed");manifest_guard()
  need(set(text(CANDIDATE,"diff","--no-renames","--name-only").splitlines())=={MANIFEST},"manifest_drift")
  git(CANDIDATE,"add","--",MANIFEST)
  state["phase"]="manifest_verification";persist(state,None,patch)
  state["manifestVerifyExit"]=command([python,"-B","scripts/ide_development/build_manifest.py","--verify"],"manifest-verify",15)
  need(state["manifestVerifyExit"]==0,"manifest_generation_failed")
  state["phase"]="fixture_generation";persist(state,None,patch);trusted_identity()
  state["fixtureExit"]=command([python,"-B",str(TRUSTED/"scripts/gitops/generated_output_closure.py"),"--generate-fixtures"],"fixture",30,
   {"PYTHONPATH":str(TRUSTED/"scripts/gitops")+":"+str(TRUSTED)})
  need(state["fixtureExit"]==0,"fixture_generation_failed")
  need(stable_fixture(json.loads(regular(CANDIDATE,FIXTURE).read_bytes()))==stable_fixture(baseline_fixture()),"fixture_drift")
  git(CANDIDATE,"add","--",FIXTURE);state["preparedIndexTree"]=derivative_guard()
  state["candidateContentTree"]=json.loads(regular(CANDIDATE,FIXTURE).read_bytes())["candidateTree"]
  state["generatedOutputs"]={rel:{"mode":"100644","gitBlob":entries(state["preparedIndexTree"])[rel][1],"sha256":digest(regular(CANDIDATE,rel))} for rel in sorted(ALLOWED)}
  patch=git(CANDIDATE,"diff","--cached","--no-ext-diff","--no-textconv","--binary","--full-index",SOURCE,"--",MANIFEST,FIXTURE)
  need(len(patch)<=384*1024,"artifact_invalid")
  state["sourcePreserved"]=True;persist(state,None,patch)
  state["phase"]="focused_tests";persist(state,None,patch);control_identity()
  result_path=PRIVATE/"native-results.json"
  state["testExit"]=command([python,"-I","-B",str(CONTROL/REPORTER)],"tests",90,
   {"SCANNER_SOURCE_ROOT":str(CANDIDATE),"SCANNER_RESULT_FILE":str(result_path)})
  control_identity();need(digest(regular(CONTROL,REPORTER))==REPORTER_SHA,"control_identity_failed")
  result_path=regular(PRIVATE,"native-results.json");need(result_path.stat().st_size<=96*1024,"focused_result_invalid")
  raw_tests=json.loads(result_path.read_bytes());positive=validate_results(raw_tests,state["preparedIndexTree"]);tests=raw_tests
  state.update(testResultsConfirmed=True,testsRun=tests["testsRun"],newTestsPassed=tests["namedNewPassed"],nativeSkipped=tests["nativeSkipEvents"],
   nativeFailures=tests["nativeFailureEvents"],nativeErrors=tests["nativeErrorEvents"])
  need(state["testExit"]==0 and positive,"focused_tests_failed")
  state["phase"]="post_identity";need(derivative_guard()==state["preparedIndexTree"],"source_changed");control_identity()
  state.update(phase="complete",code="passed",passed=True)
 except Exception as error:
  state["code"]=str(error) if type(error) is Stop and str(error) in CODES else "internal_failure"
 finally:
  try:
   control_identity()
   if state["preparedIndexTree"] is not None: need(derivative_guard()==state["preparedIndexTree"],"source_changed")
   else: source_identity();physical(TREE)
   state["sourcePreserved"]=True
  except Exception:
   state.update(sourcePreserved=False,passed=False)
   if state["code"] in {"passed","not_started"}: state["code"]="source_changed"
  persist(state,tests,patch)
 if not state["passed"]: raise Stop(state["code"])
def artifact():
 control_identity()
 state_path=regular(SAFE,"identity.json");need(state_path.stat().st_size<=16*1024 and digest(state_path)==os.environ["IDENTITY_SHA"],"artifact_invalid")
 state=json.loads(state_path.read_bytes());fixed=fixed_state()
 mutable={"phase","code","passed","dependencyExit","manifestExit","manifestVerifyExit","fixtureExit","testExit","preparedIndexTree","candidateContentTree","generatedOutputs","sourcePreserved","testsRun","newTestsPassed","testResultsConfirmed","nativeSkipped","nativeFailures","nativeErrors"}
 need(type(state) is dict and set(state)==set(fixed) and all(type(state[k]) is type(v) and state[k]==v for k,v in fixed.items() if k not in mutable),"artifact_invalid")
 need(type(state["phase"]) is str and state["phase"] in PHASES and type(state["code"]) is str and state["code"] in CODES
  and type(state["passed"]) is bool and type(state["sourcePreserved"]) is bool and type(state["testResultsConfirmed"]) is bool,"artifact_invalid")
 for key in ("dependencyExit","manifestExit","manifestVerifyExit","fixtureExit","testExit"):
  need(state[key] is None or type(state[key]) is int and -255<=state[key]<=255,"artifact_invalid")
 for key in ("testsRun","newTestsPassed","nativeSkipped","nativeFailures","nativeErrors"): need(bounded_int(state[key]),"artifact_invalid")
 tree=state["preparedIndexTree"]
 need(tree is None or type(tree) is str and re.fullmatch("[0-9a-f]{40}",tree),"artifact_invalid")
 patch_path=regular(SAFE,"generated.patch");need(patch_path.stat().st_size<=384*1024 and digest(patch_path)==os.environ["PATCH_SHA"],"artifact_invalid")
 patch=patch_path.read_bytes();values={"identity.json":state_path.read_bytes(),"generated.patch":patch}
 if tree is not None:
  need(derivative_guard()==tree,"source_changed")
  need(type(state["candidateContentTree"]) is str and re.fullmatch("[0-9a-f]{40}",state["candidateContentTree"])
   and state["candidateContentTree"]==json.loads(regular(CANDIDATE,FIXTURE).read_bytes())["candidateTree"],"artifact_invalid")
  expected_outputs={rel:{"mode":"100644","gitBlob":entries(tree)[rel][1],"sha256":digest(regular(CANDIDATE,rel))} for rel in sorted(ALLOWED)}
  need(type(state["generatedOutputs"]) is dict and state["generatedOutputs"]==expected_outputs,"artifact_invalid")
  need(patch==git(CANDIDATE,"diff","--cached","--no-ext-diff","--no-textconv","--binary","--full-index",SOURCE,"--",MANIFEST,FIXTURE),"artifact_invalid")
 else: need(patch==b"" and state["candidateContentTree"] is None and state["generatedOutputs"] is None,"artifact_invalid")
 tests=None
 if os.environ.get("TESTS_SHA","none")!="none":
  path=regular(SAFE,"tests.json");need(path.stat().st_size<=96*1024 and digest(path)==os.environ["TESTS_SHA"] and tree is not None,"artifact_invalid")
  tests=json.loads(path.read_bytes());validate_results(tests,tree);values["tests.json"]=path.read_bytes()
 need(state["testResultsConfirmed"]==(tests is not None),"artifact_invalid")
 if tests is not None:
  need(state["testsRun"]==tests["testsRun"] and state["newTestsPassed"]==tests["namedNewPassed"]
   and state["nativeSkipped"]==tests["nativeSkipEvents"] and state["nativeFailures"]==tests["nativeFailureEvents"]
   and state["nativeErrors"]==tests["nativeErrorEvents"],"artifact_invalid")
 if state["passed"]:
  need(os.environ["RUN_OUTCOME"]=="success" and os.environ["ACTUAL_PASS"]=="true" and tree is not None
   and tests is not None and tests["passed"] and state["sourcePreserved"] and state["phase"]=="complete" and state["code"]=="passed"
   and state["testsRun"]==73 and state["newTestsPassed"]==15 and state["nativeSkipped"]==state["nativeFailures"]==state["nativeErrors"]==0
   and all(state[k]==0 for k in ("dependencyExit","manifestExit","manifestVerifyExit","fixtureExit","testExit")),"artifact_invalid")
 need(not SEALED.exists() and not SEALED.is_symlink() and sum(map(len,values.values()))<=512*1024,"artifact_invalid");SEALED.mkdir(mode=0o700)
 for name,data in values.items(): (SEALED/name).write_bytes(data);(SEALED/name).chmod(0o600)
 emit(upload="true",passed="true" if state["passed"] else "false")
def main():
 try:
  need(len(sys.argv)==2 and sys.argv[1] in {"run","artifact"},"internal_failure");globals()[sys.argv[1]]();return 0
 except Exception as error:
  code=str(error) if type(error) is Stop and str(error) in CODES else "internal_failure"
  print("official_scanner_"+code,file=sys.stderr);return 1
if __name__=="__main__": sys.exit(main())
