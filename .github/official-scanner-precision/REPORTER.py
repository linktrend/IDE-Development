"""Hosted-only native unittest result projection; never serialize assertion values."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import unittest
from importlib.metadata import version

ROOT=Path(os.environ["SCANNER_SOURCE_ROOT"]).resolve()
OUT=Path(os.environ["SCANNER_RESULT_FILE"])
MODULE="scripts.tests.test_fixture_aware_secret_scan"
TEST_PATH="scripts/tests/test_fixture_aware_secret_scan.py"
TEST_SHA="60312dff41f52e0939021a6d1806a20e42cfecef84b975a83705b9c426ffb905"
EXPECTED=["CodeExpressionTests.test_callable_keyword_arguments_are_not_credentials","CodeExpressionTests.test_bash_parameter_defaults_exclude_operator_from_secret_value","CodeExpressionTests.test_non_parameter_value_keeps_leading_dash","ChangedPathStatusTests.test_copy_status_includes_source_and_destination","ChangedPathStatusTests.test_rename_status_includes_source_and_destination","ChangedPathStatusTests.test_malformed_copy_status_fails_closed","ChangedPathStatusTests.test_delete_and_invalid_copy_paths_remain_fail_closed","ChangedPathStatusTests.test_declared_migration_deletion_is_included","ChangedPathStatusTests.test_undeclared_migration_deletion_fails_closed","PackagingContractTests.test_schemas_index_manifest_and_fast_cover_scanner","PackagingContractTests.test_checked_in_fixture_declaration_binds_current_candidate_tree","PackagingContractTests.test_doctrine_and_installer_docs_name_fixture_contract","AcU1001SyntheticLiteralTests.test_declared_synthetic_assignment_passes_without_syntax_evasion","AcU1004ExactScopeTests.test_same_bytes_in_other_file_line_field_or_production_path_fail","AcU1005FailClosedTests.test_one_byte_change_fails_closed","AcU1005FailClosedTests.test_stale_digest_fails_closed","AcU1005FailClosedTests.test_renamed_file_fails_closed","AcU1005FailClosedTests.test_duplicated_value_fails_closed","AcU1005FailClosedTests.test_duplicate_fixture_ids_cannot_hide_stale_declaration","AcU1005FailClosedTests.test_unknown_rule_fails_closed","AcU1005FailClosedTests.test_undeclared_fixture_fails_closed","AcU1006RealisticFormatsTests.test_realistic_formats_cannot_be_approved","AcU1007AggregationTests.test_one_run_reports_all_findings_and_fixture_errors","AcU1008BindingTests.test_tree_or_policy_change_invalidates_until_refresh","AcU1008BindingTests.test_changed_package_source_refreshes_binding_without_oscillation","AcU1002NoBlindSpotTests.test_production_path_and_test_directory_are_both_scanned","AcU1002NoBlindSpotTests.test_missing_or_malformed_declaration_fails_closed","AcU1009RepositoryScannersTests.test_repository_owned_scanner_failure_remains_blocking","AcU1009RepositoryScannersTests.test_fixture_declaration_cannot_suppress_repository_scanner","AcU1003MigrationHelperTests.test_migration_identifies_candidates_and_never_writes_approval","CliAggregationTests.test_cli_writes_aggregate_result_and_nonzero_on_findings","AdversarialRepairTests.test_directory_symlink_and_option_like_path_use_index_identities","AdversarialRepairTests.test_suffix_named_text_and_utf16_are_scanned","AdversarialRepairTests.test_declaration_bytes_and_notes_cannot_hide_credentials","AdversarialRepairTests.test_unquoted_env_yaml_short_and_escaped_secrets","AdversarialRepairTests.test_quoted_member_and_call_references_are_not_assignment_findings","AdversarialRepairTests.test_six_credential_formats_remain_blocking","AdversarialRepairTests.test_huge_input_and_scanner_timeout_are_typed_results","AdversarialRepairTests.test_schema_extras_and_typed_failures_match_result_schema","AdversarialRepairTests.test_undecodable_nul_content_fails_closed","AdversarialRepairTests.test_binary_and_high_control_content_is_typed_nonblocking_skip","AdversarialRepairTests.test_bound_bytes_must_match_detected_value","AdversarialRepairTests.test_matching_bytes_still_approve_synthetic_only","ChangeScopedEvidenceTests.test_changed_credential_blocks_and_unchanged_finding_is_inherited","ChangeScopedEvidenceTests.test_unchanged_pre_existing_credential_is_permitted","ChangeScopedEvidenceTests.test_unchanged_baseline_fixture_declaration_is_inherited","ChangeScopedEvidenceTests.test_changed_source_cannot_use_inherited_fixture_row","ChangeScopedEvidenceTests.test_ten_thousand_approved_inherited_findings_do_not_force_full_rescan","ChangeScopedEvidenceTests.test_identity_config_and_managed_path_drift_fail_closed","ChangeScopedEvidenceTests.test_expected_managed_edit_is_scanned_but_unrelated_dirty_state_blocks","ChangeScopedEvidenceTests.test_installer_manifest_destinations_are_allowed_but_unrelated_dirty_is_not","ChangeScopedEvidenceTests.test_untracked_installer_manifest_destination_is_allowed_but_unrelated_is_not","ChangeScopedEvidenceTests.test_generated_manifest_and_declared_migration_cleanup_are_allowed_but_unrelated_paths_block","ChangeScopedEvidenceTests.test_absent_declared_migration_path_is_allowed_but_absent_unrelated_path_blocks","ChangeScopedEvidenceTests.test_rename_is_scope_ambiguity_not_an_ignore","ChangeScopedEvidenceTests.test_path_scoped_result_emits_real_head_identity","ChangeScopedEvidenceTests.test_full_scan_omits_candidate_commit_identity","ChangeScopedEvidenceTests.test_extracted_managed_root_uses_packaged_policy_paths","TypedPublicCredentialReferencePrecisionTests.test_public_marker_predicates_are_not_private_key_material","TypedPublicCredentialReferencePrecisionTests.test_short_invalid_bytes_envelope_is_format_data","TypedPublicCredentialReferencePrecisionTests.test_bare_header_and_stored_marker_remain_blocking","TypedPublicCredentialReferencePrecisionTests.test_real_and_ambiguous_envelopes_remain_blocking","TypedPublicCredentialReferencePrecisionTests.test_valid_private_key_der_body_remains_blocking","TypedPublicCredentialReferencePrecisionTests.test_public_marker_does_not_hide_other_markers_or_secrets","TypedPublicCredentialReferencePrecisionTests.test_complete_encrypted_binding_is_a_reference","TypedPublicCredentialReferencePrecisionTests.test_malformed_binding_does_not_mask_nested_assignment","TypedPublicCredentialReferencePrecisionTests.test_runtime_private_key_requires_exact_manager_path","TypedPublicCredentialReferencePrecisionTests.test_typed_references_preserve_all_other_credential_detectors","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_accepts_public_contexts_without_new_fixtures","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_keeps_real_material_and_entropy_blocking","TypedPublicCredentialReferencePrecisionTests.test_generic_entropy_inside_valid_manager_reference_blocks","TypedPublicCredentialReferencePrecisionTests.test_generic_entropy_inside_valid_encrypted_binding_blocks","TypedPublicCredentialReferencePrecisionTests.test_full_index_scan_does_not_accept_opaque_reference_components"]
NEW={name for name in EXPECTED if name.startswith("TypedPublicCredentialReferencePrecisionTests.")}
ERRORS={"AssertionError","ValueError","TypeError","KeyError","IndexError","RuntimeError","OSError","FileNotFoundError",
 "PermissionError","TimeoutError","TimeoutExpired","CalledProcessError","ImportError","ModuleNotFoundError","SyntaxError","other"}
def need(ok):
 if not ok: raise RuntimeError("focused_contract_rejected")
def valid_path(path):
 return type(path) is str and 0<len(path)<=384 and re.fullmatch("[A-Za-z0-9._/-]+",path) is not None and not path.startswith("/") and all(x not in {"",".",".."} for x in path.split("/"))
def indexed():
 p=subprocess.run(["git","ls-files","--stage","-z"],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10,check=False)
 need(p.returncode==0 and len(p.stdout)<=16*1024*1024);result={}
 for entry in p.stdout.split(b"\0"):
  if entry:
   meta,raw=entry.split(b"\t",1);mode,oid,stage=meta.decode().split();path=raw.decode()
   if mode in {"100644","100755"} and stage=="0" and valid_path(path): result[path]=oid
 return result
INDEX=indexed()
LINE_COUNTS={}
def coordinate(filename,line):
 try:
  path=Path(filename);relative=path.relative_to(ROOT).as_posix()
  if relative not in INDEX or not valid_path(relative) or type(line) is not int or not 0<line<=10000000: return None
  current=ROOT
  for part in relative.split("/"):
   current/=part
   if current.is_symlink(): return None
  need(stat.S_ISREG(current.lstat().st_mode) and current.stat().st_size<=8*1024*1024)
  if relative not in LINE_COUNTS:
   raw=current.read_bytes()
   need(hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==INDEX[relative])
   LINE_COUNTS[relative]=len(raw.splitlines())
  if line>LINE_COUNTS[relative]: return None
  return {"path":relative,"line":line}
 except Exception: return None
def test_id(test):
 name=type(test).__name__+"."+getattr(test,"_testMethodName","")
 need(name in EXPECTED);return name
def frames(err):
 locations=[];seen=set();tb=err[2]
 while tb is not None:
  row=coordinate(tb.tb_frame.f_code.co_filename,tb.tb_lineno);tb=tb.tb_next
  if row and (row["path"],row["line"]) not in seen:
   seen.add((row["path"],row["line"]))
   if len(locations)<4: locations.append(row)
 error=type(err[1]).__name__
 return error if error in ERRORS else "other",locations,max(0,len(seen)-len(locations))
class SafeResult(unittest.TestResult):
 def __init__(self):
  super().__init__();self.rows={};self.subtestFailureCount=0
 def _exc_info_to_string(self,err,test): return "redacted"
 def startTest(self,test):
  key=test_id(test);need(key not in self.rows)
  self.rows[key]={"test":key,"outcome":"started","errorType":None,"locations":[],"omittedLocations":0,"errorEvents":0}
  super().startTest(test)
 def event(self,test,outcome,err=None):
  row=self.rows[test_id(test)];row["outcome"]=outcome
  if err:
   error,locations,omitted=frames(err);row.update(errorType=error,locations=locations,omittedLocations=omitted,errorEvents=row["errorEvents"]+1)
 def addSuccess(self,test): super().addSuccess(test);self.event(test,"passed")
 def addFailure(self,test,err): super().addFailure(test,err);self.event(test,"failed",err)
 def addError(self,test,err): super().addError(test,err);self.event(test,"error",err)
 def addSkip(self,test,reason): super().addSkip(test,"redacted");self.event(test,"skipped")
 def addExpectedFailure(self,test,err): super().addExpectedFailure(test,err);self.event(test,"expected_failure",err)
 def addUnexpectedSuccess(self,test): super().addUnexpectedSuccess(test);self.event(test,"unexpected_success")
 def addSubTest(self,test,subtest,err):
  super().addSubTest(test,subtest,err)
  if err is not None:
   self.subtestFailureCount+=1;self.event(test,"failed" if issubclass(err[0],test.failureException) else "error",err)
def flatten(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite): yield from flatten(item)
  else: yield item
def main():
 import jsonschema
 need(version("jsonschema")=="4.26.0")
 need(hashlib.sha256((ROOT/TEST_PATH).read_bytes()).hexdigest()==TEST_SHA)
 sys.path.insert(0,str(ROOT))
 suite=unittest.defaultTestLoader.loadTestsFromName(MODULE)
 declared=[test_id(test) for test in flatten(suite)]
 need(len(declared)==73 and len(set(declared))==73 and set(declared)==set(EXPECTED) and len(NEW)==15)
 result=SafeResult();result.startTestRun()
 try: suite.run(result)
 finally: result.stopTestRun()
 rows=[result.rows[k] for k in sorted(result.rows)]
 counts={key:sum(row["outcome"]==key for row in rows) for key in ("started","passed","failed","error","skipped","expected_failure","unexpected_success")}
 positive=(result.wasSuccessful() and result.testsRun==73 and counts["passed"]==73 and all(counts[k]==0 for k in counts if k!="passed")
  and all(result.rows.get(k,{}).get("outcome")=="passed" for k in NEW))
 value={"schemaVersion":1,"kind":"official-scanner-native-unittest-results","module":MODULE,"testFile":TEST_PATH,
  "testsRun":result.testsRun,"counts":counts,"nativeFailureEvents":len(result.failures),"nativeErrorEvents":len(result.errors),
  "nativeSkipEvents":len(result.skipped),"nativeExpectedFailures":len(result.expectedFailures),"nativeUnexpectedSuccesses":len(result.unexpectedSuccesses),
  "subtestFailureEvents":result.subtestFailureCount,"namedNewCount":15,"namedNewPassed":sum(result.rows.get(k,{}).get("outcome")=="passed" for k in NEW),
  "passed":positive,"records":rows,"startupError":None,"rawAssertionsIncluded":False,"rawMessagesIncluded":False,"rawValuesIncluded":False}
 data=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
 need(len(data)<=96*1024 and not OUT.exists() and not OUT.is_symlink())
 OUT.write_bytes(data);OUT.chmod(0o600)
 return 0 if positive else 1
if __name__=="__main__":
 try: sys.exit(main())
 except Exception:
  try:
   error,locations,omitted=frames(sys.exc_info())
   value={"schemaVersion":1,"kind":"official-scanner-native-unittest-results","module":MODULE,"testFile":TEST_PATH,
    "testsRun":0,"counts":{key:0 for key in ("started","passed","failed","error","skipped","expected_failure","unexpected_success")},
    "nativeFailureEvents":0,"nativeErrorEvents":0,"nativeSkipEvents":0,"nativeExpectedFailures":0,"nativeUnexpectedSuccesses":0,
    "subtestFailureEvents":0,"namedNewCount":15,"namedNewPassed":0,"passed":False,"records":[],
    "startupError":{"errorType":error,"locations":locations,"omittedLocations":omitted},
    "rawAssertionsIncluded":False,"rawMessagesIncluded":False,"rawValuesIncluded":False}
   data=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
   if len(data)<=96*1024 and not OUT.exists() and not OUT.is_symlink(): OUT.write_bytes(data);OUT.chmod(0o600)
  except Exception: pass
  print("official_scanner_test_contract_failed",file=sys.stderr);sys.exit(1)
