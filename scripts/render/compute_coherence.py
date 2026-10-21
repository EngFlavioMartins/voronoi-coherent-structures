"""Geometry for the website render: Voronoi coherence of double-gyre tracers.

Runs the README's dense example (784 tracers, 101 frames over t = 0-20,
seed 7) with this package, then writes for ParaView:
  cells.vtp   Voronoi cells at t = 20, clipped to the domain and shrunk
              slightly towards their centroids, with the colour chi
  trails.vtp  the last TRAIL frames of every fourth tracer, with a radius
              that tapers towards the tail
  heads.vtp   the same tracers at t = 20
"""
import json
from pathlib import Path

import cmcrameri.cm as cmc
import numpy as np
import pyvista as pv
from scipy.spatial import Voronoi

from voronoi_coherence import analyse, integrate_double_gyre, seed_particles

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "render"
SIDE, FRAMES, DURATION, SEED = 28, 101, 20.0, 7
SHRINK, STRIDE, TRAIL, LIFT = 0.9, 4, 8, 0.004

times = np.linspace(0, DURATION, FRAMES)
tracks = integrate_double_gyre(seed_particles(SIDE, SEED), times)
result = analyse(tracks, times)
chi = result.chi
print(f"{tracks.shape[1]} tracers, eigengap {result.eigengap:.2e}")

# Voronoi cells at the last frame inside [0, 2] x [0, 1]: mirror the points across the four walls
p = tracks[-1]
mirrored = np.vstack([p, p * [-1, 1], p * [1, -1], [4, 0] + p * [-1, 1], [0, 2] + p * [1, -1]])
vor = Voronoi(mirrored)
points, faces = [], []
for i in range(len(p)):
    poly = np.clip(vor.vertices[vor.regions[vor.point_region[i]]], [0, 0], [2, 1])
    c = poly.mean(axis=0)
    poly = c + SHRINK * (poly - c)
    start = len(points)
    points.extend(np.column_stack([poly, np.zeros(len(poly))]))
    faces.append([len(poly), *range(start, start + len(poly))])
cells = pv.PolyData(np.array(points), faces=np.hstack(faces))
cells.cell_data["chi"] = chi

pick = np.arange(0, tracks.shape[1], STRIDE)
pts, lines, radius = [], [], []
for k in pick:
    start = len(pts)
    seg = tracks[-TRAIL:, k]
    pts.extend(np.column_stack([seg, np.full(TRAIL, LIFT)]))
    radius.extend(np.linspace(0.0005, 0.0034, TRAIL))       # thin tail, full width at the head
    lines.append([TRAIL, *range(start, start + TRAIL)])
trails = pv.PolyData(np.array(pts), lines=np.hstack(lines))
trails["radius"] = np.array(radius)
heads = pv.PolyData(np.column_stack([tracks[-1, pick], np.full(len(pick), LIFT)]))

OUT.mkdir(parents=True, exist_ok=True)
cells.save(OUT / "cells.vtp")
trails.save(OUT / "trails.vtp")
heads.save(OUT / "heads.vtp")
(Path(__file__).parent / "lipari.json").write_text(json.dumps(
    {"lipari": [float(v) for q in np.linspace(0, 1, 65) for v in (2 * q - 1, *cmc.lipari(0.08 + 0.84 * q)[:3])]}))
print("wrote", OUT)
