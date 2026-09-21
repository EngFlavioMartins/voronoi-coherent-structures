"""Independent implementation of the diagnostic in Martins & Rival (2021), Eqs. 3–6.

The full off-diagonal dissimilarity is A_ij = 2**(-n_ij), including pairs
that never share a Voronoi edge (n_ij = 0). It is NOT an affinity matrix.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh
from scipy.spatial import Voronoi, QhullError


def double_gyre_velocity(t, positions, amplitude=0.1, epsilon=0.25, period=10.0):
    """Divergence-free analytical double gyre on [0,2] × [0,1].

    Uses u = -dψ/dy, v = dψ/dx for ψ = A sin(π f) sin(π y).
    In particular v contains sin(π y), not cos(π y).
    """
    if not np.isfinite([amplitude, epsilon, period]).all() or amplitude <= 0 or period <= 0:
        raise ValueError("amplitude and period must be finite and positive")
    p = np.asarray(positions, dtype=float)
    x, y = p[..., 0], p[..., 1]
    a = epsilon * np.sin(2 * np.pi * t / period)
    f = a * x*x + (1 - 2*a) * x
    dfdx = 2*a*x + 1 - 2*a
    return np.stack((-np.pi*amplitude*np.sin(np.pi*f)*np.cos(np.pi*y),
                     np.pi*amplitude*np.cos(np.pi*f)*np.sin(np.pi*y)*dfdx), axis=-1)


def seed_particles(side=20, seed=7):
    """One jittered tracer in each of side² equal-area bins; fixed random seed."""
    if not isinstance(side, (int, np.integer)) or side < 2:
        raise ValueError("side must be an integer >= 2")
    rng = np.random.default_rng(seed)
    x, y = np.meshgrid(np.arange(side), np.arange(side), indexing="xy")
    return (np.column_stack((x.ravel(), y.ravel())) + rng.uniform(0.12, 0.88, (side*side, 2))) * [2/side, 1/side]


def integrate_double_gyre(initial, times, *, amplitude=0.1, epsilon=0.25,
                          period=10.0, max_step=0.05, rtol=1e-9, atol=1e-11):
    """Integrate tracers with DOP853; return (sample, particle, coordinate)."""
    p = np.asarray(initial, dtype=float)
    times = np.asarray(times, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2 or len(p) < 4 or not np.isfinite(p).all():
        raise ValueError("initial must contain at least four finite 2D points")
    if times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("times must be a finite, strictly increasing 1D array")
    if np.any(p < [0, 0]) or np.any(p > [2, 1]):
        raise ValueError("double-gyre particles must lie inside [0,2] × [0,1]")
    def rhs(t, flat):
        return double_gyre_velocity(t, flat.reshape(-1, 2), amplitude, epsilon, period).ravel()
    sol = solve_ivp(rhs, (times[0], times[-1]), p.ravel(), t_eval=times,
                    method="DOP853", rtol=rtol, atol=atol, max_step=max_step)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.T.reshape(len(times), len(p), 2)


def neighbour_counts(tracks):
    """Count shared Voronoi ridges (edges in 2D, faces in 3D) per frame.

    Particle identities must be consistent. Missing positions, coincident
    particles and lower-dimensional point sets are rejected, not imputed.
    """
    tracks = np.asarray(tracks, dtype=float)
    if tracks.ndim != 3 or tracks.shape[-1] not in (2, 3):
        raise ValueError("tracks must have shape (frames, particles, 2 or 3)")
    frames, n, dim = tracks.shape
    if frames < 2 or n < dim + 2 or not np.isfinite(tracks).all():
        raise ValueError("need >=2 finite frames and >=dimension+2 particles")
    counts = np.zeros((n, n), dtype=np.int64)
    for frame, points in enumerate(tracks):
        if len(np.unique(points, axis=0)) != n:
            raise ValueError(f"coincident particles at frame {frame}")
        if np.linalg.matrix_rank(points - points.mean(axis=0)) < dim:
            raise ValueError(f"lower-dimensional particle set at frame {frame}")
        try:
            # Voronoi ridges avoid counting a spurious diagonal in co-circular cells.
            diagram = Voronoi(points)
        except QhullError as error:
            raise ValueError(f"ill-conditioned Voronoi geometry at frame {frame}") from error
        i, j = diagram.ridge_points.T
        counts[i, j] += 1
        counts[j, i] += 1
    return counts


@dataclass
class CoherenceResult:
    counts: np.ndarray
    chi: np.ndarray
    eigenvalue: float
    eigengap: float
    residual: float


def spectral_colour(counts):
    """Largest eigenvector of the symmetric, degree-normalised Laplacian.

    Self-edges are zero by convention. The sign is made reproducible by
    making the largest-magnitude component positive, then scaling to [-1,1].
    """
    c = np.asarray(counts, dtype=float)
    if (c.ndim != 2 or c.shape[0] != c.shape[1] or len(c) < 3
            or not np.isfinite(c).all() or np.any(c < 0)
            or not np.array_equal(c, c.T) or np.any(c != np.floor(c))
            or np.any(np.diag(c) != 0)):
        raise ValueError("counts must be symmetric nonnegative integers with a zero diagonal")
    adjacency = np.exp2(-c)
    np.fill_diagonal(adjacency, 0.0)
    degree = adjacency.sum(axis=1)
    if np.any(degree <= np.finfo(float).tiny):
        raise ValueError("dissimilarities underflowed: use fewer uniformly sampled frames")
    inv = 1 / np.sqrt(degree)
    laplacian = np.eye(len(c)) - adjacency * inv[:, None] * inv[None, :]
    vals, vecs = eigh(laplacian, subset_by_index=[len(c)-2, len(c)-1])
    vector = vecs[:, -1]
    if vector[np.argmax(np.abs(vector))] < 0:
        vector = -vector
    residual = np.linalg.norm(laplacian @ vector - vals[-1]*vector)
    spread = np.ptp(vector)
    chi = 2 * (vector-vector.min())/spread - 1 if spread > 1e-14 else np.zeros(len(c))
    return CoherenceResult(c.astype(np.int64), chi, float(vals[-1]), float(vals[-1]-vals[-2]), float(residual))


def analyse(tracks, times):
    """Analyse complete tracks with uniform temporal sampling (paper count convention)."""
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or len(times) != len(tracks) or len(times) < 2 or not np.isfinite(times).all():
        raise ValueError("one finite time is required for each frame")
    dt = np.diff(times)
    if np.any(dt <= 0) or not np.allclose(dt, dt[0], rtol=1e-7, atol=1e-12):
        raise ValueError("uniform increasing times are required; resample explicitly first")
    return spectral_colour(neighbour_counts(tracks))
