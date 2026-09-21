"""Run a seeded double-gyre example or analyse a complete NPZ trajectory array."""
import argparse
import json
from pathlib import Path
import numpy as np
from .core import analyse, integrate_double_gyre, seed_particles
from .plotting import save_figures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="NPZ with tracks (frames,N,2) and times (frames,)")
    parser.add_argument("--side", type=int, default=20, help="demo: side² particles (default 400)")
    parser.add_argument("--frames", type=int, default=81)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--amplitude", type=float, default=0.1)
    parser.add_argument("--epsilon", type=float, default=0.25)
    parser.add_argument("--period", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", type=Path, default=Path("outputs/demo"))
    args = parser.parse_args(argv)
    try:
        if args.input:
            with np.load(args.input, allow_pickle=False) as data:
                tracks, times = data["tracks"], data["times"]
            if tracks.ndim != 3 or tracks.shape[-1] != 2:
                raise ValueError("CLI plots require 2D tracks; the Python API also accepts 3D")
            lo, hi = tracks.min(axis=(0, 1)), tracks.max(axis=(0, 1))
            pad = 0.04 * np.maximum(hi-lo, 1e-6)
            bounds = (lo[0]-pad[0], hi[0]+pad[0], lo[1]-pad[1], hi[1]+pad[1])
        else:
            if args.frames < 2 or not np.isfinite(args.duration) or args.duration <= 0:
                raise ValueError("frames >= 2 and a finite, positive duration are required")
            times = np.linspace(0, args.duration, args.frames)
            tracks = integrate_double_gyre(seed_particles(args.side, args.seed), times,
                        amplitude=args.amplitude, epsilon=args.epsilon, period=args.period)
            bounds = (0, 2, 0, 1)
        result = analyse(tracks, times)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    args.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output / "trajectories.npz", tracks=tracks, times=times)
    np.savez_compressed(args.output / "coherence.npz", counts=result.counts, chi=result.chi)
    report = {"particles": int(tracks.shape[1]), "frames": len(times),
              "eigenvalue": result.eigenvalue, "eigengap": result.eigengap,
              "eigenpair_residual": result.residual,
              "parameters": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}}
    (args.output / "diagnostics.json").write_text(json.dumps(report, indent=2) + "\n")
    save_figures(tracks, times, result, args.output, bounds, demo=args.input is None)
    print(json.dumps(report, indent=2))
    if result.eigengap < 1e-8:
        print("Warning: nearly repeated largest eigenvalue; χ is not uniquely determined.")
    print(f"Figures and arrays written to {args.output.resolve()}")


if __name__ == "__main__":
    main()
