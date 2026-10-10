import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    import anywidget
    import traitlets

    class DraftProbe(anywidget.AnyWidget):
        draft = traitlets.Unicode("").tag(sync=True)
        focused = traitlets.Bool(False).tag(sync=True)
        _esm = """
        export default {render({model, el}) {
          const label = document.createElement('label');
          label.textContent = 'Unsent synthetic draft ';
          const input = document.createElement('input');
          input.setAttribute('aria-label', 'Unsent synthetic draft');
          input.placeholder = 'Type without submitting';
          input.value = model.get('draft');
          input.addEventListener('input', () => {model.set('draft', input.value); model.save_changes();});
          input.addEventListener('focus', () => {model.set('focused', true); model.save_changes();});
          input.addEventListener('blur', () => {model.set('focused', false); model.save_changes();});
          label.append(input); el.append(label);
        }};
        """

    probe = mo.ui.anywidget(DraftProbe())
    probe
    return (probe,)


@app.cell
def _(mo, probe):
    mo.md(f"Custom bridge acknowledgement: `{probe.value!r}`. Throwaway feasibility probe; no API or model calls.")
    return


if __name__ == "__main__":
    app.run()
