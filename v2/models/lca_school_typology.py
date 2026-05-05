#!/usr/bin/env python3
"""LCA-style school typology extraction (k-means as proxy for initial implementation).

528校 × 10学校文化次元 → 潜在クラス K=5-7 を試行し、BIC 最小モデルを選択。
本番 LCA は poLCA (R) もしくは sklearn LatentDirichletAllocation で実装予定。
本スクリプトは Phase F 入口の k-means プロキシ実装。
"""
import sqlite3
import json
import math
import sys
from pathlib import Path
from collections import defaultdict, Counter

DB = Path('/Users/nishimura+/projects/research/jpms-db/v2/jpms_v2.db')

def load_data():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    schools = db.execute("SELECT id, name_ja, religious_affiliation, gender_type, integrated_type, location_pref FROM schools_v2").fetchall()
    scores = defaultdict(dict)
    for r in db.execute("SELECT school_id, culture_dim_id, score FROM school_culture_score").fetchall():
        scores[r['school_id']][r['culture_dim_id']] = r['score']
    db.close()

    dims = ['cult_autonomy','cult_structure','cult_diversity','cult_intensity','cult_mentor',
            'cult_creativity','cult_competition','cult_community','cult_internationality','cult_spirituality']
    X = []
    meta = []
    for s in schools:
        row = [scores[s['id']].get(d, 50) for d in dims]
        X.append(row)
        meta.append(dict(s))
    return X, meta, dims

def kmeans(X, k, max_iter=100, seed=42):
    """Simple k-means implementation."""
    import random
    random.seed(seed)
    n = len(X)
    d = len(X[0])
    # init: pick k random points
    centroids = [list(X[i]) for i in random.sample(range(n), k)]
    labels = [0]*n
    for it in range(max_iter):
        new_labels = []
        for x in X:
            best_dist, best_k = float('inf'), 0
            for ki, c in enumerate(centroids):
                dist = sum((x[i]-c[i])**2 for i in range(d))
                if dist < best_dist:
                    best_dist = dist; best_k = ki
            new_labels.append(best_k)
        if new_labels == labels:
            break
        labels = new_labels
        # update centroids
        new_centroids = []
        for ki in range(k):
            members = [X[i] for i in range(n) if labels[i]==ki]
            if not members:
                new_centroids.append(centroids[ki])
                continue
            new_centroids.append([sum(m[i] for m in members)/len(members) for i in range(d)])
        centroids = new_centroids
    # WSS
    wss = 0
    for x, lab in zip(X, labels):
        c = centroids[lab]
        wss += sum((x[i]-c[i])**2 for i in range(d))
    return labels, centroids, wss


def main():
    X, meta, dims = load_data()
    print(f"N = {len(X)}, dims = {len(dims)}")

    # Try k = 3..8
    print("\n=== Cluster selection (WSS, BIC-like) ===")
    print(f"{'k':>3} {'WSS':>12} {'BIC_proxy':>14}")
    results = {}
    for k in range(3, 9):
        labels, centroids, wss = kmeans(X, k, seed=42)
        # BIC proxy: WSS + k*log(n)*d (penalty grows with k)
        bic = wss + k*math.log(len(X))*len(dims)
        print(f"{k:>3} {wss:>12.0f} {bic:>14.0f}")
        results[k] = (labels, centroids, wss, bic)

    # Pick min BIC
    best_k = min(results, key=lambda k: results[k][3])
    print(f"\nBest k = {best_k}")

    labels, centroids, wss, bic = results[best_k]

    # Cluster profile analysis
    print(f"\n=== Cluster profiles (k={best_k}) ===")
    cluster_counts = Counter(labels)
    for ki in range(best_k):
        members = [meta[i] for i in range(len(meta)) if labels[i]==ki]
        print(f"\nCluster {ki}: {len(members)} schools ({len(members)*100/len(meta):.1f}%)")
        # centroid
        print(f"  Centroid: " + " ".join(f"{dims[i].replace('cult_',''):8s}={centroids[ki][i]:.0f}" for i in range(len(dims))))
        # demographics
        rel_counter = Counter(m['religious_affiliation'] for m in members)
        gen_counter = Counter(m['gender_type'] for m in members)
        print(f"  Religion: {dict(rel_counter.most_common(3))}")
        print(f"  Gender: {dict(gen_counter)}")
        # sample names
        sample = [m['name_ja'] for m in members[:5]]
        print(f"  Sample: {', '.join(sample)}")

    # Save typology to DB
    db = sqlite3.connect(DB)
    db.execute("DELETE FROM school_typology_lca")
    for i, (m, lab) in enumerate(zip(meta, labels)):
        db.execute("""INSERT INTO school_typology_lca
            (school_id, typology_class, posterior_prob, computed_at, model_version)
            VALUES (?,?,?,?,?)""",
            (m['id'], f'class_{lab}', 1.0, '2026-05-05', 'kmeans_v0_proxy_k'+str(best_k)))
    db.commit()
    print(f"\nSaved {len(meta)} typology assignments to school_typology_lca")
    db.close()

    # Save model output JSON
    model_output = {
        'k': best_k,
        'wss': wss,
        'bic': bic,
        'centroids': centroids,
        'dims': dims,
        'cluster_sizes': dict(cluster_counts),
        'method': 'kmeans_v0_proxy',
    }
    with open(Path(__file__).parent / 'lca_results.json', 'w') as f:
        json.dump(model_output, f, ensure_ascii=False, indent=2)
    print(f"\nWrote lca_results.json")


if __name__ == '__main__':
    main()
