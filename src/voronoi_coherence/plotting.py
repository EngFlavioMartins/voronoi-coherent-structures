"""Vector plots of computed Voronoi cells and trajectories; no raster dependencies."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import Voronoi

INK, TEAL, PURPLE, PAPER = "#24283e", "#288f91", "#7960af", "#f4f5f8"
CMAP = LinearSegmentedColormap.from_list("coherence", [PURPLE, "#ebe8ef", TEAL])


def bounded_cells(points, bounds=(0, 2, 0, 1)):
    """Clip Voronoi half-planes to a rectangle, including unbounded hull cells."""
    xmin, xmax, ymin, ymax = bounds
    adjacency = [set() for _ in points]
    for i, j in Voronoi(points).ridge_points:
        adjacency[i].add(j)
        adjacency[j].add(i)
    cells = []
    for i, p in enumerate(points):
        poly = np.array([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
        for j in sorted(adjacency[i]):
            normal = points[j] - p
            offset = (points[j] @ points[j] - p @ p)/2
            clipped = []
            if len(poly) == 0:
                break
            for a, b in zip(poly, np.roll(poly, -1, axis=0)):
                da, db = a @ normal - offset, b @ normal - offset
                if da <= 1e-13:
                    clipped.append(a)
                if (da < 0 < db) or (db < 0 < da):
                    clipped.append(a + (b-a)*da/(da-db))
            poly = np.asarray(clipped).reshape(-1, 2)
        cells.append(poly)
    return cells


def _field(ax, tracks, index, chi, bounds, trails=True):
    points = tracks[index]
    cells = bounded_cells(points, bounds)
    collection = PolyCollection(cells, array=chi, cmap=CMAP, clim=(-1, 1),
                                edgecolors="#ffffff", linewidths=0.55, alpha=0.94)
    ax.add_collection(collection)
    if trails and index > 0:
        # Each short curve follows one of the integrated tracers, not a decorative spiral.
        start = max(0, index - max(3, len(tracks)//12))
        for particle in range(0, tracks.shape[1], max(1, tracks.shape[1]//48)):
            trail = tracks[start:index+1, particle]
            ax.plot(trail[:, 0], trail[:, 1], color=INK, lw=1.0, alpha=0.72)
            if len(trail) > 1:
                ax.annotate("", xy=trail[-1], xytext=trail[-2],
                            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0, mutation_scale=12))
    ax.scatter(points[:, 0], points[:, 1], s=1.6, color=INK, alpha=0.5, linewidths=0)
    ax.set(xlim=bounds[:2], ylim=bounds[2:], aspect="equal")
    return collection


def save_figures(tracks, times, result, out, bounds=(0, 2, 0, 1), *, demo=True):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path",
                         "svg.hashsalt": "voronoi-coherence", "text.color": INK,
                         "axes.labelcolor": INK, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 1, figsize=(9, 13), constrained_layout=True)
    for ax, idx in zip(axes, [0, len(times)//2, len(times)-1]):
        field = _field(ax, tracks, idx, result.chi, bounds)
        ax.set(title=f"t = {times[idx]:g}", xlabel="x", ylabel="y")
    fig.colorbar(field, ax=axes, shrink=0.55, label="Spectral colour χ (arbitrary sign)")
    fig.suptitle("Neighbour persistence along particle trajectories")
    for suffix in ["svg", "png"]:
        fig.savefig(out / f"coherence.{suffix}", dpi=170, metadata={"Date": None} if suffix == "svg" else None)
    plt.close(fig)

    # A compact, deliberately typographic-free diagram for repository/site headers.
    fig = plt.figure(figsize=(9.6, 6), facecolor=PAPER)
    ax = fig.add_axes([0.035, 0.055, 0.93, 0.89])
    _field(ax, tracks, len(times)-1, result.chi, bounds)
    ax.set_axis_off()
    # The embedding caption supplies the method, sample count and time. Keep the
    # compact header free of microtext so the coherent motion stays legible.
    fig.savefig(out / "header.svg", facecolor=PAPER, metadata={"Date": None})
    fig.savefig(out / "header.png", facecolor=PAPER, dpi=150)
    plt.close(fig)
    for name in ["coherence.svg", "header.svg"]:
        svg = out / name
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
