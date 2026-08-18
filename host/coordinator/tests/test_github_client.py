import base64
import json
import unittest

from host.coordinator.github_client import Backoff, GitHubClient, GitHubError, GitHubResponse, validate_main_approval


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        return self.responses.pop(0)


class GitHubClientTests(unittest.TestCase):
    def test_etag_not_modified_is_noop(self):
        transport = FakeTransport([{ "status": 304, "etag": '"same"', "not_modified": True }])
        client = GitHubClient("test-secret", transport=transport)
        result = client.poll("/repos/owner/repo/pulls", etag='"same"')
        self.assertTrue(result.response.not_modified)
        self.assertEqual(result.message, "not-modified")
        self.assertEqual(transport.calls[0][2]["If-None-Match"], '"same"')

    def test_missing_token_fails_closed_without_app_fallback(self):
        client = GitHubClient("")
        with self.assertRaises(GitHubError) as error:
            client.request("GET", "/repos/owner/repo")
        self.assertEqual(error.exception.code, "automation_credentials_blocked")

    def test_protected_policy_ignores_candidate_ref(self):
        policy = {"schemaVersion": 1, "deliveryMode": "phase-integration"}
        encoded = base64.b64encode(json.dumps(policy).encode()).decode()
        transport = FakeTransport([
            {"status": 200, "payload": {"default_branch": "development"}},
            {"status": 200, "payload": {"content": encoded}},
        ])
        client = GitHubClient("test-secret", transport=transport)
        loaded, branch = client.load_protected_policy("owner/repo", candidate_ref="refs/pull/9/head")
        self.assertEqual(loaded, policy)
        self.assertEqual(branch, "development")
        self.assertIn("ref=development", transport.calls[1][1])
        self.assertNotIn("refs/pull/9/head", transport.calls[1][1])

    def test_rate_limit_is_bounded_and_failed_closed(self):
        transport = FakeTransport([{ "status": 429 }])
        client = GitHubClient("test-secret", transport=transport, backoff=Backoff(5, 20))
        result = client.poll("/repos/owner/repo/pulls", failures=2)
        self.assertTrue(result.failed_closed)
        self.assertEqual(result.next_delay_seconds, 20)

    def test_bugbot_observation_is_get_only(self):
        transport = FakeTransport([{ "status": 200, "payload": [] }])
        client = GitHubClient("test-secret", transport=transport)
        client.observe_bugbot("owner/repo", 4)
        self.assertEqual(transport.calls[0][0], "GET")
        self.assertNotIn("Bugbot", json.dumps(transport.calls[0][3]))

    def test_changed_main_binding_is_rejected(self):
        valid = {"stagingSourceSha": "a" * 40, "mainBaseSha": "b" * 40, "prHeadSha": "c" * 40, "receiptIdentity": "receipt-1"}
        validate_main_approval(valid, staging_source_sha="a" * 40, main_base_sha="b" * 40, pr_head_sha="c" * 40, receipt_identity="receipt-1")
        with self.assertRaises(GitHubError):
            validate_main_approval(valid, staging_source_sha="d" * 40, main_base_sha="b" * 40, pr_head_sha="c" * 40, receipt_identity="receipt-1")

    def test_cursor_bugbot_context_cannot_be_forged(self):
        client = GitHubClient("test-secret", transport=FakeTransport([]))
        with self.assertRaises(GitHubError):
            client.publish_status("owner/repo", "a" * 40, "Linktrend Review Gate", "success", "forged", "https://example.invalid/evidence")


if __name__ == "__main__":
    unittest.main()
