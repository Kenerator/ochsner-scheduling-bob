"""Sequential local HTTP completion sample; not browser paint or a load test."""
import argparse
from http.client import HTTPConnection
import json
import math
from pathlib import Path
import platform
import tempfile
from threading import Thread
from time import perf_counter

from mock_lifecycle import OwnedMock
from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.local_transport import make_server


def measure(samples=30):
    if type(samples) is not int or not 1<=samples<=200:
        raise ValueError("Use 1 through 200 sequential samples.")
    with OwnedMock() as mock,tempfile.TemporaryDirectory(prefix="bob-latency-") as temporary:
        service=InteractionService(lambda:HttpMockAdapter(mock.base_url),Path(temporary)/"effects.json")
        server=make_server(service,port=0)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        def post(path,body,token=None):
            connection=HTTPConnection("127.0.0.1",server.server_port,timeout=5)
            try:
                connection.request("POST",path,json.dumps(body),{"Content-Type":"application/json",**({"Authorization":"Bearer "+token} if token else {})})
                response=connection.getresponse();payload=json.loads(response.read())
                if response.status not in (200,201):raise RuntimeError("Local measurement failed.")
                return payload
            finally:connection.close()
        try:
            token=post("/create",{})["token"]
            elapsed=[];view={"revision":0}
            for index in range(samples):
                before=perf_counter()
                view=post("/text",{"text":"providers primary_care downtown" if index%2==0 else "help","revision":view["revision"]},token)
                elapsed.append((perf_counter()-before)*1000)
            ordered=sorted(elapsed)
            return {"samples":samples,"mode":"offline_commands","measurement":"sequential loopback JSON request through unchanged supplied HTTP and response decode",
                "environment":f"{platform.system()} {platform.machine()} Python {platform.python_version()}",
                "p50_ms":round(ordered[math.ceil(samples*.5)-1],3),"p95_ms":round(ordered[math.ceil(samples*.95)-1],3),"max_ms":round(ordered[-1],3),
                "target_ms":400,"p95_within_target":ordered[math.ceil(samples*.95)-1]<400,
                "browser_feedback":"not measured by this script; UI paints Working synchronously before fetch",
                "live_effects":len(view["history"]),"final_revision":view["revision"]}
        finally:server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--samples",type=int,default=30)
    print(json.dumps(measure(parser.parse_args().samples)),flush=True)
