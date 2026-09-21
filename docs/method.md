# Method notes

For each uniformly sampled frame, SciPy constructs a Voronoi tessellation. Pairs sharing a ridge contribute one to the symmetric count matrix n. In two dimensions the ridge is an edge; in three it is a face.

The implementation follows the full-matrix reading of Eqs. 3–6 in [Martins & Rival](https://arxiv.org/html/2103.09884v2):

- Aᵢⱼ = 2^(−nᵢⱼ), i ≠ j; Aᵢᵢ = 0.
- Dᵢᵢ = Σⱼ Aᵢⱼ.
- L = I − D^(−1/2) A D^(−1/2).
- χ is the eigenvector for the largest eigenvalue, rescaled to [−1,1].

A is a **dissimilarity**, not a conventional affinity. Pairs that never neighbour have Aᵢⱼ = 1; they are not removed. The paper also describes Delaunay topology, so this dense-matrix choice is made explicit. Self-loops are omitted.

Eigenvector sign is arbitrary. A deterministic sign convention helps repeatability; a near-zero largest-eigenvalue gap signals an ambiguous colour field. Sampling rate changes n and therefore the diagnostic. Do not compare differently sampled datasets as though they used an identical metric.

## Analytical flow

The demo uses the standard streamfunction ψ = A sin(πf) sin(πy), f = ε sin(2πt/T)x² + [1−2ε sin(2πt/T)]x, with u = −∂ψ/∂y and v = ∂ψ/∂x on [0,2] × [0,1]. The default A = 0.1, ε = 0.25 and T = 10 are illustrative parameters.

In particular, v contains **sin(πy)**, ensuring impermeable horizontal boundaries and zero divergence. This uses the streamfunction definition in [Shadden, Lekien & Marsden (2005)](https://doi.org/10.1016/j.physd.2005.10.007), rather than the apparent cosine typo in the later preprint's displayed Eq. 10.

DOP853 integrates trajectories at tight tolerances. The integration step and diagnostic sampling interval are independent. All header trails come from these integrated trajectories; cell colours come from χ, not hand-assigned labels.

## Limits

Missing or broken tracks are rejected. Particle identities must remain consistent. Nearly degenerate geometry can be ill-conditioned; no random jitter is silently added to measured inputs.

The dense spectral solve uses O(N²) storage and up to O(N³) work. The examples target hundreds of particles, not million-particle datasets. The count-based exponential can underflow for very long, constantly neighbouring records. No automatic rescaling is applied.

Clipping Voronoi cells to plotting bounds is only a display operation; it does not alter neighbour counts. No FTLE, experimental data interpolation, or discrete-cluster labelling is implemented.
