"""Add the LaTeX colour bar (chi) to the Voronoi coherence render.

Usage: python compose_coherence.py <raw png> <output stem>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlay import compose  # noqa: E402

raw, stem = Path(sys.argv[1]), Path(sys.argv[2])
compose(raw, stem, bar=dict(name="thesis_blue", vmin=-1, vmax=1, x=80, y=12, height=24, title=r"$\chi$",
                            ticks=[(0.0, "$-$1"), (1.0, "1")]))
