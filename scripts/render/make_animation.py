"""Animation for the README: Voronoi cells of double-gyre tracers, coloured by coherence.

Runs the README's dense example (784 tracers, 101 frames over t = 0-20, seed 7) with this
package, then draws the Voronoi cell of every tracer at every frame, coloured by its spectral
colour chi from the whole record (thesis_blue; the sign of chi is arbitrary). The two
coherent sets keep their colour together while the cells between them stretch and mix.
Amber dots are the tracers themselves.
Writes docs/assets/animation.webp.  Run:  python scripts/render/make_animation.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import Voronoi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(HERE)]
from gif import save_gif  # noqa: E402
from onda_style import colour  # noqa: E402
from voronoi_coherence import analyse, integrate_double_gyre, seed_particles  # noqa: E402

SIDE, FRAMES, DURATION, SEED = 28, 101, 20.0, 7
W, M, SS = 840, 12, 2                 # width, margin and supersampling in pixels


def frame(p, chi, lut, amber):
    w = W * SS
    s, m = (w - 2 * M * SS) / 2.0, M * SS
    img = Image.new("RGB", (w, int(s) + 2 * m), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    mirrored = np.vstack([p, p * [-1, 1], p * [1, -1], [4, 0] + p * [-1, 1], [0, 2] + p * [1, -1]])
    vor = Voronoi(mirrored)
    to_px = lambda q: [(m + x * s, m + (1 - y) * s) for x, y in q]  # noqa: E731
    for i in range(len(p)):
        poly = np.clip(vor.vertices[vor.regions[vor.point_region[i]]], [0, 0], [2, 1])
        draw.polygon(to_px(poly), fill=lut[i], outline=(0, 0, 0), width=3 * SS // 2)
    r = 2.2 * SS
    for x, y in to_px(p):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=amber)
    return img


def main():
    times = np.linspace(0, DURATION, FRAMES)
    tracks = integrate_double_gyre(seed_particles(SIDE, SEED), times)
    chi = analyse(tracks, times).chi
    chi = chi / np.abs(chi).max()
    lut = [tuple(int(255 * c) for c in colour("thesis_blue", 0.5 + 0.5 * x)) for x in chi]
    amber = tuple(int(255 * c) for c in colour("thesis_amber", 0.72))
    frames = [frame(tracks[k], chi, lut, amber) for k in range(FRAMES)]
    # rest on the last frame before the loop restarts
    save_gif(frames, ROOT / "docs" / "assets" / "animation.webp", fps=12, width=640, quality=55, hold=2.0)


if __name__ == "__main__":
    main()
