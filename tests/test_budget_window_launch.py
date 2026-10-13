"""Actual BOB argument/constructor boundaries; no vault, network or paid calls."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import __main__ as cli, model_budget
from test_browser_launch import serve_browser
from test_budget_window import START


class NoNetworkMock:
    base_url = "http://127.0.0.1:4010"

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class NoSocketServer:
    server_port = 0

    def serve_forever(self):
        pass

    def server_close(self):
        pass


class BudgetWindowLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.created = []

    def construct_budget(self, path, **options):
        # Keep real durability/accounting; replace only clock and project root.
        self.assertEqual(self.root / ".bob-local/model-budget.json", path)
        budget = model_budget.ModelBudget(path, clock=lambda: START + 3600, **options)
        self.created.append(budget)
        return budget

    def test_browser_explicit_flag_reaches_canonical_budget_without_request(self):
        with patch.object(serve_browser, "ROOT", self.root), \
                patch.object(serve_browser, "ModelBudget", side_effect=self.construct_budget), \
                patch.object(serve_browser, "OwnedMock", NoNetworkMock), \
                patch.object(serve_browser, "server_for_launch", return_value=NoSocketServer()), \
                patch.object(serve_browser.signal, "signal"), \
                patch("ochsner_bob.language._http_transport", side_effect=AssertionError("no startup model request")), \
                contextlib.redirect_stdout(io.StringIO()):
            code = serve_browser.main(["--openai", "--unlimited-today", "--port", "0",
                                       "--namespace", str(self.root / "effects")])
        self.assertEqual(0, code)
        self.assertEqual(1, len(self.created))
        self.assertEqual("active", self.created[0].snapshot()["unlimited_today"]["status"])
        self.assertEqual(0, self.created[0].snapshot()["calls"])

    def test_cli_explicit_flag_reaches_canonical_budget_without_request(self):
        output = io.StringIO()
        with patch.object(cli, "ROOT", self.root), \
                patch.object(cli, "ModelBudget", side_effect=self.construct_budget), \
                patch("ochsner_bob.language._http_transport", side_effect=AssertionError("no startup model request")):
            code = cli.main(["--openai", "--unlimited-today", "--journal", str(self.root / "effects.json")],
                            input_stream=io.StringIO("/quit\n"), output_stream=output)
        self.assertEqual(0, code)
        self.assertEqual(1, len(self.created))
        self.assertEqual("active", self.created[0].snapshot()["unlimited_today"]["status"])
        self.assertEqual(0, self.created[0].snapshot()["calls"])
        self.assertIn("2026-10-13T05:00:00Z", output.getvalue())

    def test_budget_opt_in_requires_explicit_model_mode_before_any_startup(self):
        for module in (cli, serve_browser):
            with self.subTest(module=module.__name__):
                error = io.StringIO()
                with patch.object(module, "ModelBudget", side_effect=AssertionError("no budget startup")), \
                        contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as caught:
                    module.main(["--unlimited-today"])
                self.assertEqual(2, caught.exception.code)
                self.assertIn("requires --openai", error.getvalue())

    def test_help_with_opt_in_flags_does_not_construct_budget_or_language(self):
        for module in (cli, serve_browser):
            with self.subTest(module=module.__name__):
                with patch.object(module, "ModelBudget", side_effect=AssertionError("no budget startup")), \
                        patch.object(module, "LanguageAdapter", side_effect=AssertionError("no model startup")), \
                        contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    module.main(["--openai", "--unlimited-today", "--help"])
                self.assertEqual(0, caught.exception.code)


if __name__ == "__main__":
    unittest.main()
