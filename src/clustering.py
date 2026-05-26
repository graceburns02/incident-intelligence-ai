from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans


def cluster_embeddings(embeddings: list[list[float]], n_clusters: int = 6, random_state: int = 42) -> list[int]:
    if len(embeddings) == 0:
        return []
    n_clusters = max(1, min(n_clusters, len(embeddings)))
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=random_state)
    labels = km.fit_predict(np.array(embeddings))
    return labels.tolist()
