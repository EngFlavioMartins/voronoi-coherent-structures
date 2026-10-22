"""ParaView (pvpython) render of the Voronoi coherence of double-gyre tracers, OpenONDA style.

Usage: pvpython render_coherence.py <output png> [width height]
Reads outputs/render/{cells,trails,heads}.vtp from compute_coherence.py.

Black background. Voronoi cells glow with thesis_blue by the spectral colour
chi (its sign is arbitrary); the shrink gap between cells stays black.
Tapered trails of recent tracer motion are thesis_amber.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from paraview.simple import Glyph, Show, Tube, XMLPolyDataReader  # noqa: E402

out = Path(sys.argv[1])
width, height = (int(a) for a in (sys.argv[2:4] if len(sys.argv) > 3 else (3600, 2250)))
DATA = HERE.parents[1] / "outputs" / "render"

view = style.setup_view(width, height)
lut = style.lut("chi", "thesis_blue", -1.0, 1.0)
d = Show(XMLPolyDataReader(FileName=[str(DATA / "cells.vtp")]), view)
style.mapped(d, "chi", lut, assoc="CELLS")
d.Interpolation = "Flat"
d.Ambient, d.Diffuse = 1.0, 0.0                 # unlit: the cells glow
lut.RescaleTransferFunction(-1.0, 1.0)

amber = style.colour("thesis_amber", 0.72)
tubes = Tube(Input=XMLPolyDataReader(FileName=[str(DATA / "trails.vtp")]))
tubes.Scalars = ["POINTS", "radius"]
tubes.VaryRadius = "By Absolute Scalar"
tubes.Radius = 1.0
tubes.NumberofSides = 10
style.solid(Show(tubes, view), amber, roughness=0.4)
heads = Glyph(Input=XMLPolyDataReader(FileName=[str(DATA / "heads.vtp")]), GlyphType="Sphere")
heads.GlyphType.Radius = 0.0052
heads.GlyphType.ThetaResolution = 16
heads.GlyphType.PhiResolution = 16
heads.ScaleArray = ["POINTS", "No scale array"]
heads.GlyphMode = "All Points"
style.solid(Show(heads, view), amber, roughness=0.4)

view.CameraPosition = [1.22, -1.62, 2.62]
view.CameraFocalPoint = [1.22, 0.47, 0.0]
view.CameraViewUp = [0, 0.75, 0.66]
view.CameraViewAngle = 30
style.save(view, out, width, height)
print(out)
