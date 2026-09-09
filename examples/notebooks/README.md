# pypgl notebooks

| notebook | contents |
| --- | --- |
| [`tour.ipynb`](tour.ipynb) | The number type and what it buys: coordinates in $\mathbb{Q}$, the refusal of `float`, and a quantitative look at the failure of the double-precision orientation predicate. Then the predicate matrix, `intersection` as a sum type, the exact/inexact split in the measures, and `Canvas`. |
| [`booleans.ipynb`](booleans.ipynb) | The regularized set operations on r-sets, Minkowski sums, and the adjoint erosion — result types, the loss of connectivity under erosion, and the support-function reading of a convex receiver. |
| [`bitmatrix.ipynb`](bitmatrix.ipynb) | Digital sets over $\mathbb{Z}^2$: digitization, packed set algebra, the region/lattice-point duality, morphological opening and closing, and connectivity under the 4/8 pairing. |
| [`motion.ipynb`](motion.ipynb) | Translational motion planning by the Lozano-Pérez–Wesley reduction: the configuration space as an erosion, the reduced visibility graph against the complete one, A\*, and two exact certificates that the motion is collision-free. |

Each is self-contained and runs top to bottom. They complement the scripts in
[`examples/`](..) rather than restating them: a script writes one SVG at the end,
while every intermediate result here renders inline through `_repr_svg_`.

`bitmatrix.ipynb` is also the only worked treatment of `BitMatrix` in the
repository — [`examples/`](..) holds one script per upstream C++ example, and
upstream has none for it. `motion.ipynb` covers the same problem as
[`example_motion.py`](../example_motion.py) but shows the intermediate state the
script cannot: one figure per stage, and its assertions checked rather than
stated.

## Running them

```bash
pip install pypgl jupyterlab
jupyter lab
```

The notebooks import nothing but `pypgl`. They are committed with their outputs,
so they read as finished pages without being executed.

## Keeping them current

After a binding change or a pgl re-pin:

```bash
make notebooks                  # from examples/
python notebooks/execute.py     # or directly; a filename runs just that one
```

This needs `nbclient` and `nbformat`. Execution stops at the first cell that
raises, so a notebook that no longer matches the library fails rather than
shipping a stale result. Re-executing an unchanged notebook produces no diff, so
anything that moves is a real change.
