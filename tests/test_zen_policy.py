"""B11/FR-013: real ZEN decisions, closed facts and safe provenance.

Mutations caught: identity/consent bypass, effect retries, permissive schema,
Python-only rules, swallowed engine failures, and CWD-dependent graph loading.
"""

import hashlib
import importlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import zen


ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "policies" / "bob.json"
DOMAINS = {
    "action": ("discover", "availability", "lookup", "booking", "handoff"),
    "identity": ("verified", "missing", "ambiguous", "unknown"),
    "proposal": ("current", "none"),
    "confirmation": ("current", "none"),
    "effect": ("clear", "blocked", "unknown"),
}


def facts(**changes):
    return dict(action="booking", identity="verified", proposal="current",
                confirmation="current", effect="clear") | changes


class ZenPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.policy"),
                             "Standalone ZEN policy implementation is missing")
        self.module = importlib.import_module("ochsner_bob.policy")
        self.policy = self.module.Policy()

    def assert_decision(self, decision, allow, rule=None):
        self.assertEqual(set(decision),
                         {"allow", "reason", "rule", "engine", "policy_digest"})
        self.assertIs(type(decision["allow"]), bool)
        self.assertIs(decision["allow"], allow)
        self.assertEqual(decision["engine"], "zen-engine")
        for key in ("reason", "rule", "policy_digest"):
            self.assertIsInstance(decision[key], str)
            self.assertTrue(decision[key])
        if rule:
            self.assertEqual(decision["rule"], rule)

    def test_real_engine_all_240_categorical_combinations(self):
        # Independent permission oracle; no production rule helpers involved.
        for values in itertools.product(*DOMAINS.values()):
            given = dict(zip(DOMAINS, values))
            action = given["action"]
            expected = {
                "discover": True,
                "availability": given["identity"] == "verified",
                "lookup": given["identity"] == "verified",
                "handoff": given["effect"] == "clear",
                "booking": values[1:] == ("verified", "current", "current", "clear"),
            }[action]
            with self.subTest(**given):
                self.assert_decision(self.policy.evaluate(given), expected)

    def test_stable_rule_and_reason_taxonomy(self):
        cases = [
            ({"action": "discover", "identity": "unknown"}, True, "public_discovery"),
            ({"action": "handoff", "identity": "missing"}, True, "handoff_ready"),
            ({"action": "lookup"}, True, "verified_read"),
            ({"identity": "ambiguous"}, False, "identity_required"),
            ({"proposal": "none"}, False, "proposal_required"),
            ({"confirmation": "none"}, False, "confirmation_required"),
            ({"effect": "blocked"}, False, "effect_blocked"),
            ({"action": "handoff", "effect": "unknown"}, False, "effect_unknown"),
            ({}, True, "booking_ready"),
        ]
        for changes, allow, rule in cases:
            with self.subTest(changes=changes):
                first = self.policy.evaluate(facts(**changes))
                self.assert_decision(first, allow, rule)
                self.assertEqual(first, self.module.Policy().evaluate(facts(**changes)))

    def test_missing_and_extra_fields_are_explicitly_denied(self):
        invalid = [{}, facts(patient_id="synthetic-only"), facts(allow=True),
                   facts(**{"unexpected": "unknown"})]
        for field in DOMAINS:
            missing = facts()
            del missing[field]
            invalid.append(missing)
        for given in invalid:
            with self.subTest(given=given):
                self.assert_decision(self.policy.evaluate(given), False, "invalid_facts")

    def test_no_coercion_of_wrong_types_or_unknown_categories(self):
        for field in DOMAINS:
            for value in (None, True, False, 0, 1, [], {}, "", "INVALID", " current "):
                with self.subTest(field=field, value=value):
                    self.assert_decision(self.policy.evaluate(facts(**{field: value})),
                                         False, "invalid_facts")
        for given in (None, [], "booking", 1, True):
            self.assert_decision(self.policy.evaluate(given), False, "invalid_facts")

    def test_input_is_not_mutated_and_private_values_are_not_echoed(self):
        given = facts(patient_id="PRIVATE_SENTINEL")
        before = dict(given)
        decision = self.policy.evaluate(given)
        self.assertEqual(given, before)
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(decision))

    def test_graph_runs_directly_in_real_zen_with_trace(self):
        decision = zen.ZenEngine().create_decision(GRAPH.read_text())
        decision.validate()
        for given, allowed in ((facts(), True), (facts(confirmation="none"), False),
                               (facts(action="discover", identity="missing"), True),
                               (facts(action="handoff", effect="blocked"), False),
                               (facts(action="unrecognized"), False), ({}, False)):
            with self.subTest(given=given):
                response = decision.evaluate(given, {"trace": True})
                self.assertIs(response["result"]["allow"], allowed)
                self.assertTrue(response["trace"])
                wrapped = self.policy.evaluate(given)
                for key in ("allow", "reason", "rule"):
                    self.assertEqual(wrapped[key], response["result"][key])

    def test_digest_is_sha256_of_exact_loaded_graph_bytes(self):
        digest = hashlib.sha256(GRAPH.read_bytes()).hexdigest()
        for given in (facts(), facts(effect="unknown"), {}):
            self.assertEqual(self.policy.evaluate(given)["policy_digest"], digest)

    def test_graph_change_changes_provenance_and_real_engine_result(self):
        document = json.loads(GRAPH.read_bytes())
        table = next(node["content"] for node in document["nodes"]
                     if node["type"] == "decisionTableNode")
        row = next(row for row in table["rules"] if row["_id"] == "booking_ready")
        row["allow"] = "false"
        changed = json.dumps(document).encode()
        # Intercept loading only; parsing and evaluation still use actual ZEN.
        with patch.object(Path, "read_bytes", return_value=changed):
            policy = self.module.Policy()
        decision = policy.evaluate(facts())
        self.assert_decision(decision, False, "booking_ready")
        self.assertEqual(decision["policy_digest"], hashlib.sha256(changed).hexdigest())
        self.assertNotEqual(decision["policy_digest"],
                            self.policy.evaluate(facts())["policy_digest"])

    def test_engine_creation_failure_is_sanitized_and_closed(self):
        with patch.object(self.module.zen, "ZenEngine", side_effect=RuntimeError("PRIVATE_SENTINEL")):
            policy = self.module.Policy()
        result = policy.evaluate(facts())
        self.assert_decision(result, False, "engine_error")
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_engine_evaluation_failure_is_sanitized_and_closed(self):
        with patch.object(self.module.zen, "ZenEngine") as engine:
            engine.return_value.create_decision.return_value.evaluate.side_effect = RuntimeError("PRIVATE_SENTINEL")
            policy = self.module.Policy()
        result = policy.evaluate(facts())
        self.assert_decision(result, False, "engine_error")
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_malformed_engine_output_cannot_be_authority(self):
        invalid = [None, {}, {"result": None},
                   {"result": {"allow": "true", "reason": "x", "rule": "x"}},
                   {"result": {"allow": True, "reason": "", "rule": "x"}},
                   {"result": {"allow": True, "reason": "x", "rule": "x", "extra": True}}]
        for response in invalid:
            with self.subTest(response=response):
                with patch.object(self.module.zen, "ZenEngine") as engine:
                    engine.return_value.create_decision.return_value.evaluate.return_value = response
                    policy = self.module.Policy()
                self.assert_decision(policy.evaluate(facts()), False, "engine_error")

    def test_real_engine_rejects_broken_graph_without_leaking_details(self):
        content = b'{"nodes":[{"id":"PRIVATE_SENTINEL","type":"invalidNode"}],"edges":[]}'
        with patch.object(Path, "read_bytes", return_value=content):
            policy = self.module.Policy()
        result = policy.evaluate(facts())
        self.assert_decision(result, False, "engine_error")
        self.assertEqual(result["policy_digest"], hashlib.sha256(content).hexdigest())
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_real_engine_runtime_failure_is_sanitized_and_closed(self):
        document = json.loads(GRAPH.read_bytes())
        node = document["nodes"][1]
        node["type"] = "functionNode"
        node["content"] = ('export const handler = () => { '
                           'throw new Error("PRIVATE_SENTINEL"); };')
        content = json.dumps(document).encode()
        # Real ZEN accepts this graph, then fails during evaluation (not load).
        decision = zen.ZenEngine().create_decision(content.decode())
        decision.validate()
        with self.assertRaises(Exception):
            decision.evaluate(facts())
        with patch.object(Path, "read_bytes", return_value=content):
            policy = self.module.Policy()
        result = policy.evaluate(facts())
        self.assert_decision(result, False, "engine_error")
        self.assertEqual(result["policy_digest"], hashlib.sha256(content).hexdigest())
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_missing_policy_file_fails_closed(self):
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError("PRIVATE_SENTINEL")):
            policy = self.module.Policy()
        result = policy.evaluate(facts())
        self.assert_decision(result, False, "engine_error")
        self.assertEqual(result["policy_digest"], "unavailable")
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_editable_install_loads_policy_without_pythonpath(self):
        # -I removes CWD/PYTHONPATH, leaving the actual editable install to work.
        code = ("import json; from ochsner_bob.policy import Policy; "
                f"print(json.dumps(Policy().evaluate({facts()!r})))")
        result = subprocess.run([sys.executable, "-I", "-B", "-c", code], cwd=ROOT / "policies",
                                check=True, capture_output=True, text=True)
        self.assert_decision(json.loads(result.stdout), True, "booking_ready")


if __name__ == "__main__":
    unittest.main()
