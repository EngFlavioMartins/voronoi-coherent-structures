import numpy as np
import matplotlib.pyplot as plt
from voronoi_coherence.core import seed_particles
from voronoi_coherence.plotting import _field


def test_header_keeps_cells_and_trails_without_arrows():
    points = seed_particles(4, 7)
    tracks = np.stack([points, points + [.001, 0]])
    fig, ax = plt.subplots()
    field = _field(ax, tracks, 1, np.linspace(-1, 1, len(points)),
                   (0, 2, 0, 1), arrows=False)
    assert len(field.get_paths()) == len(points)
    assert len(ax.lines) > 0
    assert not ax.texts  # Arrow annotations must not obscure the coloured cells.
    plt.close(fig)
