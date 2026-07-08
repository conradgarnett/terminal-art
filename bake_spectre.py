#!/usr/bin/env python3
"""
bake_spectre.py — offline geometry + ML step for hat.py.

Generates a patch of "the spectre" aperiodic monotile, clusters the tiles
by their local neighborhood with k-means, and writes spectre_tiling.json
(tile polygons + a cluster label per tile). hat.py then just reads that
file and colors by cluster, staying pure standard library at runtime.

The idea: an aperiodic tiling never repeats globally, but it has only
finitely many distinct local neighborhoods. Fingerprinting each tile's
surroundings (rotation-invariant) and clustering them recovers those
recurring "local motifs" — a small bit of unsupervised ML that exposes
the hidden order in a pattern that, by construction, never repeats.

Requires: hat-amp, numpy, scipy, scikit-learn (all offline only).
Run:  python3 bake_spectre.py
"""

import json
import os

import numpy as np
from scipy.spatial import cKDTree
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from hat_amp.spectre import generate_spectre_tiling

LEVEL = 4          # substitution depth (bigger = larger patch)
K_NEIGHBORS = 6    # neighbors per tile in the fingerprint
N_CLUSTERS = 8     # number of local-motif classes to find
CROP_RADIUS = 42.0  # keep tiles within this radius of center (covers any view)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "spectre_tiling.json")


def main():
    tiles = [np.asarray(t, float) for t in generate_spectre_tiling(LEVEL)]
    n = len(tiles)
    cents = np.array([t.mean(0) for t in tiles])
    # each tile's own orientation (centroid -> first vertex) for invariance
    orient = np.array([np.arctan2(*(tiles[i][0] - cents[i])[::-1])
                       for i in range(n)])

    tree = cKDTree(cents)
    _, nn = tree.query(cents, k=K_NEIGHBORS + 1)  # +1 for self
    feats = np.zeros((n, K_NEIGHBORS * 2))
    for i in range(n):
        idxs = [j for j in nn[i] if j != i][:K_NEIGHBORS]
        off = cents[idxs] - cents[i]
        a = -orient[i]
        c, s = np.cos(a), np.sin(a)
        loc = np.stack([off[:, 0] * c - off[:, 1] * s,
                        off[:, 0] * s + off[:, 1] * c], 1)
        loc = loc[np.argsort(np.arctan2(loc[:, 1], loc[:, 0]))]
        feats[i, :loc.size] = loc.flatten()

    X = StandardScaler().fit_transform(feats)
    labels = KMeans(n_clusters=N_CLUSTERS, n_init=10,
                    random_state=0).fit_predict(X)

    ox, oy = cents.mean(0)
    out = []
    for i in range(n):
        if np.hypot(cents[i, 0] - ox, cents[i, 1] - oy) > CROP_RADIUS:
            continue
        pts = [[round(float(x - ox), 4), round(float(y - oy), 4)]
               for x, y in tiles[i]]
        out.append({"k": int(labels[i]), "p": pts})

    with open(OUT, "w") as fh:
        json.dump({"nclust": N_CLUSTERS, "tiles": out}, fh,
                  separators=(",", ":"))
    sizes = np.bincount(labels, minlength=N_CLUSTERS).tolist()
    print(f"baked {len(out)} tiles (of {n}) -> {OUT}")
    print(f"cluster sizes (full patch): {sizes}")


if __name__ == "__main__":
    main()
