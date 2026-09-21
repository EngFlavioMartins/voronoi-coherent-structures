# Validation record

Local environment: Python 3.12, NumPy 2.5.3, SciPy 1.18.1 and Matplotlib 3.11.2.

The test suite checks analytical boundary conditions and divergence, a tightened-step trajectory comparison, rigid translation/rotation invariance, exact spectral grouping of a constructed two-block case, full clipped-cell coverage, input rejection and 3D geometry.

For the header command in the README (784 tracers, 101 frames, t = 20, seed 7), the largest eigenvalue is approximately 1.0345884, the top eigengap is 0.0008663 and the eigenpair residual is approximately 1.36 × 10⁻¹⁵. Re-run the command to inspect the arrays and diagnostic JSON.

These checks establish implementation consistency, not experimental accuracy or a quantitative reproduction of the publication. Eigenvector signs and near-degenerate eigenspaces can vary between numerical libraries.
