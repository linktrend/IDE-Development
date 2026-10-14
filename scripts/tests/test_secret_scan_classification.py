"""Classification boundaries; no production credentials or blanket exclusions."""
import unittest
from urllib.parse import urlencode, urlunsplit
from scripts.gitops import secret_scan as scanner


class ClassificationTests(unittest.TestCase):
    def setUp(self):
        self.field = 'attempt' + 'Token'
        self.reference = '.'.join(['envelope', 'executionConstraints', 'attempt', self.field])
        self.member = self.field + ': ' + self.reference + ','
        self.token_field = 'next' + '_token'
        self.generated = self.token_field + ' = "attempt-v1-" + hashlib.sha256(f"{run_id}:{effect_id}".encode("utf-8")).hexdigest()'

    def uri(self, user='local_role', query=None, scheme='postgresql'):
        return urlunsplit((scheme, user + '@localhost', '/test_data', urlencode(query or {}), ''))

    def scan(self, text, path='sample.mjs'):
        return scanner.scan_text(path, text)

    def test_unquoted_property_reference_is_not_literal_secret(self):
        self.assertEqual(self.scan('const sample = {\n' + self.member + '\n};'), [])

    def test_quoted_data_and_non_source_files_keep_entropy_detection(self):
        for path,text in [('sample.mjs', self.field + ': "' + self.reference + '",'),
                          ('sample.env', self.field + '=' + self.reference), ('sample.jsx',self.member)]:
            with self.subTest(path=path):
                self.assertTrue(self.scan(text,path))

    def test_comments_and_template_literal_data_do_not_gain_reference_exemption(self):
        for text in ['/*\n' + self.member + '\n*/', 'const note = `\n' + self.member + '\n`;']:
            self.assertTrue(self.scan(text))

    def test_generated_runtime_hash_prefix_is_not_the_token_value(self):
        self.assertEqual(self.scan(self.generated,'worker.py'), [])

    def test_runtime_dictionary_keys_are_references_not_hash_secret_literals(self):
        text = self.generated.replace('{run_id}:{effect_id}', "{context['effect_id']}:{context['next_attempt_token']}")
        self.assertEqual(self.scan(text,'worker.py'), [])

    def test_standalone_prefix_and_static_hash_stay_blocking(self):
        literal = self.token_field + ' = "attempt-v1-"'
        static_hash = self.token_field + ' = "attempt-v1-" + hashlib.sha256(b"constant-input").hexdigest()'
        for text in [literal, static_hash]:
            self.assertTrue(self.scan(text,'worker.py'))

    def test_synthetic_marker_is_not_hidden_by_generated_reference_handling(self):
        text = self.generated.replace('attempt-v1-', scanner.SYNTHETIC_PREFIX + 'scope-check.v1:')
        self.assertTrue(self.scan(text,'worker.py'))

    def test_credential_free_postgres_endpoints_are_references(self):
        for query in [{}, {'host':'/tmp/test-socket'}, {'currentSchema':'test_schema','sslmode':'disable'}]:
            value = self.uri(query=query)
            self.assertFalse(scanner.is_realistic_value(value))
            self.assertEqual(self.scan('const location = ' + repr(value) + ';'), [])

    def test_complete_runtime_templates_without_auth_material_are_references(self):
        value = urlunsplit(('postgresql','${runtime_user}@localhost','/${runtime_database}','host=${socket_path}',''))
        self.assertEqual(self.scan('const location = `' + value + '`;'), [])

    def test_password_userinfo_remains_blocking_using_existing_fixture_namespace(self):
        marker = scanner.SYNTHETIC_PREFIX + 'negative-boundary.v1'
        for user in ['local_role:' + marker, 'local_role:', 'local_role%3Aencoded-reference']:
            self.assertTrue(self.scan(self.uri(user)))

    def test_opaque_high_entropy_username_is_not_accepted_as_endpoint_data(self):
        self.assertTrue(self.scan(self.uri(user=self.reference)))

    def test_sensitive_and_unknown_query_properties_remain_blocking(self):
        for query_property in ['password','token','authMechanismProperties','unreviewed_option']:
            self.assertTrue(self.scan(self.uri(query={query_property:scanner.SYNTHETIC_PREFIX+'negative-query.v1'})))

    def test_opaque_or_invalid_safe_query_values_are_not_blanket_exempt(self):
        for query in [{'host':self.reference},{'sslmode':'unreviewed-mode'}]:
            self.assertTrue(self.scan(self.uri(query=query)))

    def test_other_database_schemes_retain_existing_conservative_detection(self):
        for scheme in ['mysql','mongodb','mongodb+srv']:
            self.assertTrue(self.scan(self.uri(scheme=scheme)))

    def test_incomplete_template_and_missing_database_path_remain_blocking(self):
        fragment = ''.join(['postgresql', '://', '${unclosed'])
        no_database = urlunsplit(('postgresql','local_role@localhost','','',''))
        for value in [fragment,no_database]:
            self.assertTrue(self.scan(value))

    def test_literal_concatenation_cannot_hide_query_credential_material(self):
        endpoint = self.uri()
        suffix = '?password=' + scanner.SYNTHETIC_PREFIX + 'negative-split.v1'
        source = 'const connection = ' + repr(endpoint) + ' + ' + repr(suffix) + ';'
        self.assertTrue(any(r['rule']==scanner.RULE_FORMAT_DATABASE for r in self.scan(source)))

    def test_escaped_uri_fragment_is_not_treated_as_proven_endpoint(self):
        source = self.uri() + '\\?password=' + scanner.SYNTHETIC_PREFIX + 'negative-escaped.v1'
        self.assertTrue(self.scan(source))


if __name__ == '__main__':
    unittest.main()
