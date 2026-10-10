import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from ochsner_bob.widget import SchedulingWidget
    mo.ui.anywidget(SchedulingWidget())
    return


if __name__ == "__main__":
    app.run()
