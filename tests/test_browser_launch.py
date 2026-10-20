"""Subprocess launch exercises the actual owned mock and browser HTTP service."""
import json
from http.client import HTTPConnection
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import serve_browser


class BrowserLaunchTests(unittest.TestCase):
    def test_server_loop_schedules_retention_without_patient_activity(self):
        from unittest.mock import Mock
        service=Mock()
        with patch.object(serve_browser,"make_server") as server:
            result=serve_browser.server_for_launch(service,0,28450)
            self.assertIs(result,server.return_value)
            result.service_actions()
            result.service_actions()
            self.assertEqual(service.maintain_retention.call_count,2)

    def test_offline_launcher_does_not_construct_language_or_budget(self):
        with patch.object(serve_browser,"LanguageAdapter") as language, patch.object(serve_browser,"ModelBudget") as budget:
            self.assertIsNone(serve_browser.language_for_launch(False))
            language.assert_not_called()
            budget.assert_not_called()

    def test_explicit_openai_uses_the_one_project_ledger_without_dispatch(self):
        with patch.object(serve_browser,"LanguageAdapter") as language, patch.object(serve_browser,"ModelBudget") as budget:
            self.assertIs(serve_browser.language_for_launch(True),language.return_value)
            budget.assert_called_once_with(serve_browser.ROOT/".bob-local/model-budget.json", application_runtime=False,
                _existing_only=True, _existing_writes=True)
            language.assert_called_once_with(budget=budget.return_value)
            language.return_value.interpret.assert_not_called()

    def test_owned_backend_starts_and_serves_shared_conversation(self):
        root=Path(__file__).resolve().parents[1]
        script=root/"scripts/serve_browser.py"
        self.assertTrue(script.is_file(),"owned browser backend launch missing")
        with tempfile.TemporaryDirectory() as temporary:
            # README prerequisite: create the private parent before a nested
            # namespace; the launcher creates only its immediate run directory.
            parent = Path(temporary) / ".bob-local"
            parent.mkdir(mode=0o700)
            child=subprocess.Popen([sys.executable,str(script),"--port","0","--namespace",str(parent/"run-N")],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertTrue(select.select([child.stdout],[],[],5)[0],"backend startup exceeded bound")
                line=child.stdout.readline()
                self.assertTrue(line.startswith("BOB local backend ready: "),line)
                port=int(line.rsplit(":",1)[1])
                connection=HTTPConnection("127.0.0.1",port,timeout=3)
                connection.request("POST","/create",body="{}",headers={"Content-Type":"application/json"})
                response=connection.getresponse()
                self.assertEqual(response.status,201)
                created=json.loads(response.read());connection.close()
                connection=HTTPConnection("127.0.0.1",port,timeout=3)
                connection.request("POST","/text",body=json.dumps({"text":"providers primary_care downtown","revision":0}),headers={"Content-Type":"application/json","Authorization":"Bearer "+created["token"]})
                response=connection.getresponse(); result=json.loads(response.read());connection.close()
                self.assertEqual(response.status,200)
                self.assertEqual(result["state"],"providers")
                self.assertEqual(result["providers"][0]["name"],"Dr. Elena Brooks")
            finally:
                child.terminate()
                child.communicate(timeout=5)
                self.assertIsNotNone(child.returncode)
