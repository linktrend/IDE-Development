"""Exercise retained shell packaging and retirement without remote operations."""
from __future__ import annotations

import re
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from gitops.coordinator.receipts import (
    compute_candidate_identity, compute_receipt_digest, compute_transition_digest,
    create_full_suite_receipt, create_transition_receipt,
)


class MainPromotionShellTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.real_git = shutil.which('git')
        self.git('init', '-b', 'issue/501-shell-proof')
        self.git('config', 'user.name', 'Offline fixture')
        self.git('config', 'user.email', 'offline@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.hooksPath', '/dev/null')
        (self.repo / '.github/workflows').mkdir(parents=True)
        (self.repo / '.github/linktrend-delivery-mode.json').write_text('{"offlineFixture":true}\n')
        (self.repo / '.github/workflows/offline-fixture.yml').write_text('name: Offline fixture\n')
        (self.repo / 'fixture-lock.json').write_text('{"version":1}\n')
        self.git('add', '.')
        self.git('commit', '-m', 'offline main fixture')
        self.base = self.git('rev-parse', 'HEAD')
        (self.repo / 'feature.txt').write_text('accepted Development content\n')
        self.git('add', 'feature.txt')
        self.git('commit', '-m', 'offline accepted Development')
        self.head = self.git('rev-parse', 'HEAD')
        self.branch = 'promote/main/' + self.head[:12]
        self.git('config', 'remote.origin.url', 'https://example.invalid/owner/name.git')
        for branch, sha in [('main', self.base), ('development', self.head)]:
            self.git('update-ref', 'refs/remotes/origin/' + branch, sha)
        self.identity = compute_candidate_identity(self.repo, ['fixture-lock.json'], 'full', profile_files=['.github/linktrend-delivery-mode.json'], source_branch='development').to_dict()
        self.receipt = self.make_receipt(self.identity)
        self.store = self.root / 'receipts'
        self.store.mkdir()
        self.receipt_path = self.store / (self.identity['gitTree'] + '-full-gate.json')
        self.fake_bin = self.root / 'fake-bin'
        self.fake_bin.mkdir()
        self.log = self.root / 'calls.jsonl'
        self.tempfiles = self.root / 'tempfiles'
        self.tempfiles.mkdir()
        self.install_fake_tools()

    def git(self, *args):
        result = subprocess.run([self.real_git, *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def make_receipt(self, identity):
        return create_full_suite_receipt({'schemaVersion': 2, 'candidateIdentity': identity, 'workflowRunId': 501, 'workflowRunAttempt': 1, 'runnerLabel': 'ubuntu-24.04-arm', 'startedAt': '2026-10-15T01:00:00Z', 'completedAt': '2026-10-15T01:01:00Z', 'conclusion': 'success', 'commandDigest': 'sha256:' + 'a' * 64, 'evidenceDigests': {'evidence/full.log': 'sha256:' + 'b' * 64}}).to_dict()

    def install_fake_tools(self):
        script = '''#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
tool, args = pathlib.Path(sys.argv[0]).name, sys.argv[1:]
command = args[2:] if args[:1] == ['-C'] else args
record = {'tool': tool, 'args': args}
if tool == 'git' and command[:1] == ['push']:
    cwd = args[1] if args[:1] == ['-C'] else os.getcwd()
    record['headAtPush'] = subprocess.check_output([os.environ['OFFLINE_REAL_GIT'], '-C', cwd, 'rev-parse', 'HEAD'], text=True).strip()
with open(os.environ['OFFLINE_CALL_LOG'], 'a') as handle:
    handle.write(json.dumps(record) + '\\n')
if tool == 'git':
    if command[:1] == ['fetch']:
        raise SystemExit(0)
    if command[:1] == ['push']:
        if command != ['push', '-u', 'origin', 'HEAD:refs/heads/' + os.environ['OFFLINE_BRANCH']]:
            raise SystemExit('forbidden protected or unexpected push')
        raise SystemExit(0)
    if command[:1] == ['merge']:
        raise SystemExit('forbidden synthetic merge candidate')
    if command == ['merge-base', '--is-ancestor', 'origin/main', 'origin/development'] and os.environ.get('OFFLINE_NOT_ANCESTOR'):
        raise SystemExit(1)
    raise SystemExit(subprocess.run([os.environ['OFFLINE_REAL_GIT'], *args]).returncode)
if args[:2] == ['pr', 'list']:
    print('[]')
elif args[:2] == ['pr', 'create']:
    print('https://example.invalid/owner/name/pull/77')
elif args[:2] == ['pr', 'view']:
    print('77')
elif args[:2] == ['pr', 'checks']:
    print(json.dumps([{'name': name, 'state': 'SUCCESS'} for name in ['Linktrend Receipt Gate', 'Linktrend Branch Source Policy']]))
else:
    raise SystemExit('forbidden gh action: ' + ' '.join(args))
'''
        for name in ('git', 'gh'):
            path = self.fake_bin / name
            path.write_text(script)
            path.chmod(0o755)

    def run_shell(self, **extra):
        self.receipt_path.write_text(json.dumps(self.receipt))
        env = {'PATH': str(self.fake_bin) + os.pathsep + os.environ.get('PATH', os.defpath), 'HOME': str(self.root), 'TMPDIR': str(self.tempfiles), 'LANG': 'C.UTF-8', 'LINKTREND_CONTROLLER_ROLE': 'program-lead', 'MODE': 'package', 'AUTOMATION_TOKEN': 'ltfx.offline.normal-token', 'AUTOMATION_TOKEN_SOURCE': 'github_token', 'GH_REPO': 'owner/name', 'EXPECTED_DEVELOPMENT_SHA': self.head, 'EXPECTED_PROMOTE_HEAD': self.head, 'EXPECTED_MAIN_SHA': self.base, 'PROMOTE_PR_NUMBER': '77', 'LINKTREND_COORDINATOR_RECEIPT_ROOT': str(self.store), 'RECEIPT_DEPENDENCY_FILES': 'fixture-lock.json', 'OUTCOME_FILE': str(self.root / 'outcome.json'), 'GATE_WAIT_SECONDS': '0', 'OFFLINE_CALL_LOG': str(self.log), 'OFFLINE_REAL_GIT': self.real_git, 'OFFLINE_BRANCH': self.branch}
        env.update(extra)
        return subprocess.run(['/bin/bash', str(ROOT / 'scripts/gitops/promote_main.sh')], cwd=self.repo, env=env, capture_output=True, text=True, timeout=20)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def assert_no_publication(self):
        self.assertFalse(any(c['tool'] == 'gh' and c['args'][:2] in (['pr', 'create'], ['pr', 'merge']) for c in self.calls()))
        self.assertFalse(any(c['tool'] == 'git' and 'push' in c['args'] for c in self.calls()))

    def test_legacy_approve_rejects_valid_role_shas_receipt_and_green_checks_before_tools(self):
        # Valid metadata cannot supply the missing Principal approval object.
        result = self.run_shell(MODE='approve-merge', RECEIPT_PATH=str(self.receipt_path))
        self.assertEqual(result.returncode, 1)
        self.assertIn('shell approve-merge is disabled', result.stderr)
        self.assertIn('delivery_controller.py complete-main', result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.root / 'outcome.json').exists())

    def test_package_preserves_exact_development_transition_and_canonical_receipt(self):
        phase = {**self.identity, 'sourceBranch': 'phase/accepted', 'headCommit': 'c' * 40}
        self.receipt = self.make_receipt(phase)
        transition = create_transition_receipt(self.receipt, target_branch='development', target_commit=self.head, target_tree=self.identity['gitTree'], protected_base_commit=self.base).to_dict()
        transition_path = self.root / 'transition.json'
        transition_path.write_text(json.dumps(transition))
        result = self.run_shell(LINKTREND_TRANSITION_RECEIPT_PATH=str(transition_path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / 'outcome.json').read_text())['status'], 'packaged')
        creates = [c['args'] for c in self.calls() if c['tool'] == 'gh' and c['args'][:2] == ['pr', 'create']]
        self.assertEqual(len(creates), 1)
        body = creates[0][creates[0].index('--body') + 1]
        marker = json.loads(re.search(r'<!-- linktrend-promote:\s*(\{.*?\})\s*-->', body, re.S).group(1))
        self.assertEqual(marker['sourceSha'], self.head)
        self.assertEqual(marker['candidateHead'], self.head)
        self.assertEqual(marker['targetSha'], self.base)
        self.assertEqual(marker['candidateIdentity'], self.identity)
        self.assertEqual(marker['transitionReceipt'], transition)
        self.assertEqual(marker['transitionReceiptDigest'], compute_transition_digest(transition))
        self.assertEqual(marker['receiptDigest'], compute_receipt_digest(self.receipt))
        pushes = [c for c in self.calls() if c['tool'] == 'git' and 'push' in c['args']]
        self.assertEqual(len(pushes), 1)
        self.assertEqual(pushes[0]['headAtPush'], self.head)
        self.assertEqual(pushes[0]['args'][-1], 'HEAD:refs/heads/' + self.branch)
        self.assertFalse(any(c['tool'] == 'gh' and c['args'][:2] == ['pr', 'merge'] for c in self.calls()))
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.assertEqual(json.loads(self.receipt_path.read_text()), self.receipt)
        self.assertEqual(list(self.tempfiles.iterdir()), [])

    def test_package_holds_nonancestor_without_publishing(self):
        result = self.run_shell(OFFLINE_NOT_ANCESTOR='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / 'outcome.json').read_text())['status'], 'blocked')
        self.assert_no_publication()
        self.assertEqual(list(self.tempfiles.iterdir()), [])

    def test_package_rejects_invalid_full_identity_before_publishing(self):
        self.receipt = self.make_receipt({**self.identity, 'dependencyDigest': 'sha256:' + 'd' * 64})
        result = self.run_shell()
        self.assertIn('dependency_mismatch', result.stdout)
        self.assert_no_publication()
        self.assertEqual(list(self.tempfiles.iterdir()), [])

    def test_reevaluate_reports_waiting_without_package_or_merge_mutation(self):
        result = self.run_shell(MODE='reevaluate')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        outcome = json.loads((self.root / 'outcome.json').read_text())
        self.assertEqual(outcome['status'], 'waiting')
        self.assertIn('delivery_controller.py complete-main', outcome['detail'])
        self.assert_no_publication()
        self.assertFalse(any(c['tool'] == 'git' and 'worktree' in c['args'] for c in self.calls()))


if __name__ == '__main__':
    unittest.main()
