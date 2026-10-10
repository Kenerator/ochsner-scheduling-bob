"""Thin Marimo widget; domain state lives only in the loopback sidecar."""
from pathlib import Path
import base64
import anywidget
import traitlets


class SchedulingWidget(anywidget.AnyWidget):
    _esm = Path(__file__).with_name("widget.js")
    # A static reviewed local image, never a remote tracking URL or user HTML.
    logo = traitlets.Unicode().tag(sync=True)

    def __init__(self, **kwargs):
        root=Path(__file__).resolve().parents[2]
        logo=(root/"assets/ui/branding/ochsner-health-observed.svg").read_bytes()
        super().__init__(logo="data:image/svg+xml;base64,"+base64.b64encode(logo).decode("ascii"),**kwargs)
