#!/usr/bin/env python3
"""Re-run the notebooks in this directory, in place.

The notebooks are committed *with* their outputs, so GitHub renders their
figures and a reader gets the whole thing without running anything. That only
works if the outputs stay true, which is what this script is for: run it after
changing a binding or re-pinning pgl, and commit whatever moved. A cell that
raises stops the run, so a stale notebook fails loudly rather than quietly
shipping a wrong picture.

    python execute.py              # every notebook here
    python execute.py tour.ipynb   # just one

Needs `pip install nbclient nbformat`; the notebooks themselves need only pypgl.
Per-cell execution timings are stripped afterwards so that re-running an
unchanged notebook produces no diff at all.
"""

import pathlib
import re
import sys

import nbformat
from nbclient import NotebookClient

HERE = pathlib.Path(__file__).parent

# A Canvas has no operator<<, so its plain-text repr is the default
# `<pypgl._pgl.Canvas at 0x7f...>` -- a memory address, different every run.
# Jupyter never shows it, having the SVG to display instead, so it is dropped
# rather than left to make every re-run look like a change.
ADDRESS = re.compile(r"^<[\w.]+ at 0x[0-9a-f]+>$")


def tidy(cell):
    cell.metadata.pop("execution", None)       # wall-clock stamps: pure diff noise
    for output in cell.get("outputs", []):
        data = output.get("data", {})
        if "image/svg+xml" in data and ADDRESS.match(data.get("text/plain", "").strip()):
            del data["text/plain"]


def run(path):
    nb = nbformat.read(path, as_version=4)
    NotebookClient(nb, kernel_name="python3", timeout=300,
                   resources={"metadata": {"path": str(path.parent)}}).execute()
    for cell in nb.cells:
        tidy(cell)
    nbformat.write(nb, path)
    print(f"{path.name}: {len(nb.cells)} cells")


if __name__ == "__main__":
    targets = [pathlib.Path(a) for a in sys.argv[1:]] or sorted(HERE.glob("*.ipynb"))
    for target in targets:
        run(target)
