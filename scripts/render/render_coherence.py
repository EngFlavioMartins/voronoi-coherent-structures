"""ParaView (pvpython) render of the Voronoi coherence of double-gyre tracers.

Usage: pvpython render_coherence.py <output png> [width height]
Reads outputs/render/{cells,trails,heads}.vtp from compute_coherence.py.
Cells: chi with Crameri's "lipari" (sign arbitrary). Trails and heads: neutral grey.
"""
import json
import sys
from pathlib import Path

from paraview.simple import (ColorBy, GetActiveViewOrCreate, GetColorTransferFunction, Glyph,
                             SaveScreenshot, Show, Tube, XMLPolyDataReader)

out = Path(sys.argv[1])
width, height = (int(a) for a in (sys.argv[2:4] if len(sys.argv) > 3 else (2400, 1600)))
HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "outputs" / "render"

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [width, height]
view.OrientationAxesVisibility = 0
view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.EnableRayTracing = 1
view.BackEnd = "OSPRay raycaster"
view.SamplesPerPixel = 32
view.AmbientSamples = 8

lut = GetColorTransferFunction("chi")
lut.RGBPoints = json.loads((HERE / "lipari.json").read_text())["lipari"]
lut.ColorSpace = "RGB"
lut.AutomaticRescaleRangeMode = "Never"
d = Show(XMLPolyDataReader(FileName=[str(DATA / "cells.vtp")]), view)
ColorBy(d, ("CELLS", "chi"))
d.LookupTable = lut
d.SetScalarBarVisibility(view, False)
d.Ambient, d.Diffuse = 0.6, 0.45
lut.RescaleTransferFunction(-1.0, 1.0)

trails = XMLPolyDataReader(FileName=[str(DATA / "trails.vtp")])
tubes = Tube(Input=trails)
tubes.Scalars = ["POINTS", "radius"]
tubes.VaryRadius = "By Absolute Scalar"
tubes.Radius = 1.0
tubes.NumberofSides = 10
d = Show(tubes, view)
d.ColorArrayName = ["POINTS", ""]
d.AmbientColor = d.DiffuseColor = [0.20, 0.23, 0.27]
d.Specular, d.SpecularPower = 0.3, 30
heads = Glyph(Input=XMLPolyDataReader(FileName=[str(DATA / "heads.vtp")]), GlyphType="Sphere")
heads.GlyphType.Radius = 0.0052
heads.GlyphType.ThetaResolution = 16
heads.GlyphType.PhiResolution = 16
heads.ScaleArray = ["POINTS", "No scale array"]
heads.GlyphMode = "All Points"
d = Show(heads, view)
d.ColorArrayName = ["POINTS", ""]
d.AmbientColor = d.DiffuseColor = [0.20, 0.23, 0.27]
d.Specular, d.SpecularPower = 0.4, 40

view.CameraPosition = [1.0, -1.45, 2.35]
view.CameraFocalPoint = [1.0, 0.47, 0.0]
view.CameraViewUp = [0, 0.75, 0.66]
view.CameraViewAngle = 30
SaveScreenshot(str(out), view, ImageResolution=[width, height], TransparentBackground=0)
print(out)
