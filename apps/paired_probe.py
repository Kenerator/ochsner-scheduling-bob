import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")

@app.cell
def _():
    import anywidget
    import marimo as mo
    from pathlib import Path
    class PairedProbe(anywidget.AnyWidget):
        _esm = Path(__file__).with_name("paired_probe.js")
    mo.ui.anywidget(PairedProbe())
    return

if __name__ == "__main__":
    app.run()
