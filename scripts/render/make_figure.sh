#!/bin/sh
# Make the website figure in outputs/render/ (PNG, WebP and PDF).
# Needs Python with the packages in the README, ParaView's pvpython and LaTeX.
# Set PVPYTHON if pvpython is not on your PATH, e.g.
#   PVPYTHON=/Applications/ParaView-6.1.0.app/Contents/bin/pvpython sh scripts/render/make_figure.sh
set -e
cd "$(dirname "$0")/../.."
PV=${PVPYTHON:-pvpython}
R=scripts/render
O=outputs/render
mkdir -p $O
python $R/compute_coherence.py
$PV $R/render_coherence.py $O/voronoi-raw.png
python $R/compose_coherence.py $O/voronoi-raw.png $O/voronoi-coherence
