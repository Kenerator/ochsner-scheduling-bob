"""Run the shipped widget's pure presentation boundary in actual JavaScript."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import tempfile


class WidgetProjectionTests(unittest.TestCase):
    def test_reference_recovery_is_operation_specific_and_mirrors_without_losing_capability(self):
        script = Path(__file__).with_name("widget_harness.mjs")
        result = subprocess.run([shutil.which("node"), str(script), "--reference-recovery"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_widget_import_is_explicit_esm_without_node_syntax_detection(self):
        path = Path(__file__).resolve().parents[1] / "src/ochsner_bob/widget.js"
        script = "import widget,{semanticReceipt} from " + json.dumps(path.as_uri()) + "; console.log(JSON.stringify({render:typeof widget.render,revision:semanticReceipt(0,{},null,0,[]).revision}));"
        environment = {**os.environ, "NODE_OPTIONS": "--no-experimental-detect-module"}
        result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script],
            env=environment, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"render": "function", "revision": 0})

    def test_actual_support_renderer_labels_pairing_and_control_separately(self):
        script=Path(__file__).with_name("widget_harness.mjs")
        result=subprocess.run([shutil.which("node"),str(script),"--support-status"],
                              capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_acknowledged_stale_notice_and_pending_controls_are_mirrored(self):
        from ochsner_bob.browser_service import BrowserService
        from test_session_contract import FixturePort
        path=Path(__file__).resolve().parents[1]/"src/ochsner_bob/widget.js"
        script="import {semanticReceipt,mirroredNotice} from "+json.dumps(path.as_uri())+"; const receipt=semanticReceipt(0,{},null,0,[],{notice:'stale',pending:true,dirty:true,can_confirm:false}); console.log(JSON.stringify({receipt,message:mirroredNotice(receipt,{message:'ordinary backend message'})}));"
        run=subprocess.run([shutil.which("node"),"--input-type=module","-e",script],capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr)
        value=json.loads(run.stdout)
        self.assertEqual(value["message"],"This screen is out of date. Review the current screen before acting.")
        with tempfile.TemporaryDirectory() as temporary:
            service=BrowserService(FixturePort,Path(temporary)/"effects.json")
            token=service.create()["token"]
            support=service.join(service.pair(token))
            service.ack(token,value["receipt"])
            mirror=service.read(support)
            self.assertTrue(mirror["fresh"])
            self.assertEqual(mirror["last_observed"]["presentation"],{"notice":"stale","pending":True,"dirty":True,"can_confirm":False})
            for presentation in ({"notice":"private arbitrary text","pending":False,"dirty":False},{"notice":"stale","pending":1,"dirty":False},{"notice":"stale","pending":False,"dirty":False,"text":"private"},{"notice":"stale","pending":False,"dirty":False,"can_confirm":1}):
                with self.assertRaises(ValueError):service.ack(token,{**value["receipt"],"presentation":presentation})

    def test_real_service_accepts_shipped_renderer_acknowledgement(self):
        from ochsner_bob.browser_service import BrowserService
        from test_session_contract import FixturePort
        path=Path(__file__).resolve().parents[1]/"src/ochsner_bob/widget.js"
        script="import {semanticReceipt} from "+json.dumps(path.as_uri())+"; console.log(JSON.stringify(semanticReceipt(0,{message:'Public draft',specialty:'primary_care',location:'downtown',start_date:'',end_date:''},'message',0,['developer'])));"
        run=subprocess.run([shutil.which("node"),"--input-type=module","-e",script],capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            service=BrowserService(FixturePort,Path(temporary)/"effects.json")
            token=service.create()["token"]
            receipt=json.loads(run.stdout)
            try:
                acknowledged=service.ack(token,receipt)
            except ValueError:
                self.fail("Shipped renderer emits an acknowledgement rejected by the real privacy boundary")
            self.assertEqual(acknowledged,{"acknowledged":0})

    def test_local_help_is_not_swallowed_during_pending_text(self):
        script=Path(__file__).with_name("widget_harness.mjs")
        result=subprocess.run([shutil.which("node"),str(script)],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_actual_support_renderer_does_not_invent_legacy_presentation_observations(self):
        script=Path(__file__).with_name("widget_harness.mjs")
        result=subprocess.run([shutil.which("node"),str(script),"--support-presentation"],
                              capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)

    def project(self,view,role="patient"):
        path=Path(__file__).resolve().parents[1]/"src/ochsner_bob/widget.js"
        self.assertTrue(path.is_file(),"shared patient/support renderer missing")
        script="import {presentation} from "+json.dumps(path.as_uri())+"; console.log(JSON.stringify(presentation("+json.dumps(view)+","+json.dumps(role)+")));"
        run=subprocess.run([shutil.which("node"),"--input-type=module","-e",script],capture_output=True,text=True,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr)
        return json.loads(run.stdout)

    def view(self):
        return {"revision":4,"identity_status":"verified","takeover":False,"booking_blocked":False,
                "providers":[{"providerId":"p1","name":"Provider Alpha"}],
                "proposal":{"id":"proposal-a","nonce":"local-only","revision":4,"slot":{"providerId":"p1","startTime":"2026-10-20T09:00:00-05:00","specialty":"primary_care","location":"downtown"}},
                "preferences":{"location":"downtown"},"history":[]}

    def test_exact_snapshot_confirmation_and_read_only_support(self):
        view=self.view()
        patient=self.project(view)
        self.assertTrue(patient["canConfirm"])
        self.assertIn("2026-10-20T09:00:00-05:00",patient["summary"])
        self.assertIn("Provider Alpha",patient["summary"])
        self.assertFalse(self.project(view,"support")["canConfirm"])
        for key,value in (("takeover",True),("booking_blocked",True),("identity_status","missing"),("revision",5)):
            changed={**view,key:value}
            self.assertFalse(self.project(changed)["canConfirm"],key)

    def test_prior_completed_outcome_does_not_become_current_rejection(self):
        view={**self.view(),"current_result":{"kind":"booking","status":"rejected"},"history":[{"kind":"booking","status":"completed"},{"kind":"booking","status":"rejected"}]}
        projected=self.project(view)
        self.assertEqual(projected["current"],"booking: rejected")
        self.assertEqual(projected["history"],["booking: completed","booking: rejected"])
