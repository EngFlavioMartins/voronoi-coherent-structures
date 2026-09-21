import json
import numpy as np
from voronoi_coherence.cli import main


def test_demo_and_imported_tracks(tmp_path):
    out = tmp_path / "demo"
    main(["--side", "3", "--frames", "5", "--duration", "0.5", "--output", str(out)])
    assert (out / "header.svg").stat().st_size > 1000
    report = json.loads((out / "diagnostics.json").read_text())
    assert report["eigenpair_residual"] < 1e-12
    main(["--input", str(out / "trajectories.npz"), "--output", str(tmp_path / "import")])
    with np.load(out / "coherence.npz") as a, np.load(tmp_path / "import/coherence.npz") as b:
        np.testing.assert_allclose(a["chi"], b["chi"])
