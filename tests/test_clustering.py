from src.clustering import cluster_embeddings


def test_cluster_embeddings_returns_label_per_record():
    embeddings = [[0.1, 0.1], [0.2, 0.2], [9.0, 9.0], [9.1, 9.2]]
    labels = cluster_embeddings(embeddings, n_clusters=2)
    assert len(labels) == 4
    assert len(set(labels)) == 2
