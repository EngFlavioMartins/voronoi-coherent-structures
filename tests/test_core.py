import numpy as np
import pytest
from voronoi_coherence.core import (analyse, double_gyre_velocity, integrate_double_gyre,
                                    neighbour_counts, seed_particles, spectral_colour)
from voronoi_coherence.plotting import bounded_cells


def test_double_gyre_no_through_flow_and_divergence():
    s = np.linspace(0, 1, 20)
    for t in [0, 1.7, 4.2]:
        assert np.max(np.abs(double_gyre_velocity(t, np.column_stack((s*0, s)))[:, 0])) < 1e-14
        assert np.max(np.abs(double_gyre_velocity(t, np.column_stack((s*0+2, s)))[:, 0])) < 1e-14
        assert np.max(np.abs(double_gyre_velocity(t, np.column_stack((s*2, s*0+1)))[:, 1])) < 1e-14
        p, h = seed_particles(4), 1e-5
        dx = (double_gyre_velocity(t, p+[h, 0])-double_gyre_velocity(t, p-[h, 0]))/(2*h)
        dy = (double_gyre_velocity(t, p+[0, h])-double_gyre_velocity(t, p-[0, h]))/(2*h)
        assert np.max(np.abs(dx[:, 0]+dy[:, 1])) < 1e-8


def test_integration_convergence_and_bounds():
    p, times = seed_particles(4), np.linspace(0, 5, 21)
    a = integrate_double_gyre(p, times, max_step=0.1)
    b = integrate_double_gyre(p, times, max_step=0.025, rtol=1e-11, atol=1e-13)
    np.testing.assert_allclose(a, b, atol=2e-8, rtol=0)
    assert np.all(a >= 0) and np.all(a <= [2, 1])


def test_neighbours_rigid_frame_invariance():
    p = seed_particles(5)
    tracks = np.repeat(p[None], 5, axis=0)
    angle = 0.723
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    shifted = tracks @ rotation + np.arange(5)[:, None, None]*[1.7, -0.8]
    c = neighbour_counts(tracks)
    np.testing.assert_array_equal(c, neighbour_counts(shifted))
    assert set(np.unique(c)) == {0, 5}
    assert np.all(c == c.T) and not np.diag(c).any()


def test_spectral_known_two_groups():
    counts = np.zeros((8, 8), dtype=int)
    counts[:4, :4] = 12
    counts[4:, 4:] = 12
    np.fill_diagonal(counts, 0)
    result = spectral_colour(counts)
    assert np.std(result.chi[:4]) < 1e-12
    assert np.std(result.chi[4:]) < 1e-12
    assert result.chi[0]*result.chi[-1] < 0
    assert result.residual < 1e-12 and 0 <= result.eigenvalue <= 2+1e-12


def test_cells_cover_domain():
    area = 0
    for poly in bounded_cells(seed_particles(8)):
        area += abs(np.dot(poly[:, 0], np.roll(poly[:, 1], 1)) - np.dot(poly[:, 1], np.roll(poly[:, 0], 1)))/2
    assert area == pytest.approx(2.0, abs=1e-10)


def test_input_rejections():
    tracks = np.repeat(seed_particles(3)[None], 3, axis=0)
    with pytest.raises(ValueError, match="uniform"):
        analyse(tracks, [0, 1, 3])
    tracks[1, 1] = tracks[1, 0]
    with pytest.raises(ValueError, match="coincident"):
        neighbour_counts(tracks)
    tracks[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        neighbour_counts(tracks)


def test_three_dimensional_tracks():
    p = np.random.default_rng(42).random((12, 3))
    tracks = np.repeat(p[None], 3, axis=0)
    result = analyse(tracks, [0, 1, 2])
    assert result.chi.shape == (12,) and result.residual < 1e-12


def test_seed_reproducibility():
    np.testing.assert_array_equal(seed_particles(10, 4), seed_particles(10, 4))
