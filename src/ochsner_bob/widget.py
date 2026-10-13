"""Thin Marimo widget; domain state lives only in the loopback sidecar."""
from pathlib import Path
import base64
import os
import re
import anywidget
import traitlets


class SchedulingWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name("widget.js")
    # A static reviewed local image, never a remote tracking URL or user HTML.
    logo = traitlets.Unicode().tag(sync=True)
    # Public loopback routing only. No key or arbitrary network destination is
    # synchronized into the browser, including on later trait assignments.
    backend_url = traitlets.Unicode("http://127.0.0.1:28451").tag(sync=True)

    @traitlets.validate("backend_url")
    def _valid_backend_url(self, proposal):
        value = proposal["value"]
        match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})", value)
        if match is None or int(match.group(1)) > 65535:
            raise ValueError("Use an explicit numeric IPv4 loopback HTTP transport URL without paths or credentials.")
        return value

    def __init__(self, **kwargs):
        root=Path(__file__).resolve().parents[2]
        logo=(root/"assets/ui/branding/ochsner-health-observed.svg").read_bytes()
        backend_url=kwargs.pop("backend_url",os.environ.get("BOB_TRANSPORT_URL","http://127.0.0.1:28451"))
        super().__init__(logo="data:image/svg+xml;base64,"+base64.b64encode(logo).decode("ascii"),backend_url=backend_url,**kwargs)
