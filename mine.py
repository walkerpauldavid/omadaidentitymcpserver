"""
Cluster AD users by similar group memberships.

Assumes a CSV with at least: user,group
(Extra columns like user_upn, user_display_name, group_dn are fine.)

Install once:
    pip install pandas scikit-learn numpy matplotlib

Run:
    python cluster_ad_users.py
"""

import os
import sys
from pathlib import Path

# Import numpy if available (some editors/linters may report unresolved imports).
# Use a fallback of None so runtime code can avoid referencing np directly.
try:
    import numpy as np
except Exception:
    np = None

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# ------------------ Config ------------------
CSV_PATH = r"C:\Temp\ad_memberships.csv"  # change if needed
OUT_DIR  = r"C:\Temp"
K        = 5  # number of clusters (try 3–10)
RANDOM_STATE = 42

# -------------- Load & sanity check ---------
p = Path(CSV_PATH)
if not p.exists():
    sys.exit(f"ERROR: CSV not found at {p}")

edges = pd.read_csv(p, dtype=str).fillna("")

# Try to detect user/group column names case-insensitively
def find_col(candidates):
    cols_lc = {c.lower(): c for c in edges.columns}
    for cand in candidates:
        if cand.lower() in cols_lc:
            return cols_lc[cand.lower()]
    return None

user_col  = find_col(["user", "samaccountname", "sAMAccountName"])
group_col = find_col(["group", "group_name", "samaccountname_group"])

if not user_col or not group_col:
    sys.exit(
        "ERROR: Could not find required columns.\n"
        f"Found columns: {edges.columns.tolist()}\n"
        "Expect at least 'user' and 'group' (case-insensitive)."
    )

edges = edges[[user_col, group_col]].rename(columns={user_col: "user", group_col: "group"})

# Drop empties/dupes just in case
edges = edges[(edges["user"] != "") & (edges["group"] != "")]
edges = edges.drop_duplicates(ignore_index=True)

user_group = (
    edges.assign(val=1)
         .pivot_table(index="user", columns="group", values="val", fill_value=0)
         .astype("uint8")
)
# --------- Build user × group matrix --------
user_group = (
    edges.assign(val=1)
         .pivot_table(index="user", columns="group", values="val", fill_value=0)
         .astype(np.uint8)
)
print("User × Group shape:", user_group.shape)

# If there’s only one user or one group, clustering won’t work
if user_group.shape[0] < 2 or user_group.shape[1] < 2:
    sys.exit("Not enough users or groups to cluster (need at least 2 users and 2 groups).")

# --------------- K-Means --------------------
model = KMeans(n_clusters=K, n_init="auto", random_state=RANDOM_STATE)
labels = model.fit_predict(user_group.values)

clusters = (
    pd.DataFrame({"user": user_group.index, "cluster": labels})
      .sort_values(["cluster", "user"], kind="stable")
      .reset_index(drop=True)
)
print("\nCluster sizes:")
print(clusters.value_counts("cluster").rename("count"))

# ------------- Cluster fingerprints ----------
# Mean membership per group within each cluster (higher = more characteristic)
fingerprints = (
    pd.DataFrame(user_group.values, index=user_group.index, columns=user_group.columns)
      .assign(cluster=labels)
      .groupby("cluster").mean().T  # groups as rows
)

# ------------- Save outputs ------------------
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
clusters_path      = Path(OUT_DIR) / "user_clusters.csv"
fingerprints_path  = Path(OUT_DIR) / "cluster_group_fingerprints.csv"
matrix_path        = Path(OUT_DIR) / "user_group_matrix.csv"

clusters.to_csv(clusters_path, index=False)
fingerprints.round(3).to_csv(fingerprints_path)
pd.DataFrame(user_group).to_csv(matrix_path)

print(f"\nSaved:")
print(f"- {clusters_path}          (each user’s cluster)")
print(f"- {fingerprints_path}      (which groups characterize each cluster)")
print(f"- {matrix_path}            (binary user×group matrix)")

# ------------- Optional: quick 2D plot -------
try:
    import matplotlib.pyplot as plt

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(user_group.values)
    xs, ys = coords[:, 0], coords[:, 1]

    plt.figure()
    for c in sorted(clusters["cluster"].unique()):
        idx = (labels == c)
        plt.scatter(xs[idx], ys[idx], label=f"Cluster {c}")
    for i, u in enumerate(user_group.index):
        # Light annotation; comment out if too busy
        plt.annotate(u, (xs[i], ys[i]), xytext=(3, 3), textcoords="offset points", fontsize=8)
    plt.title("User access similarity (PCA of user×group)")
    plt.xlabel("PC1"); plt.ylabel("PC2")
    plt.legend()
    plt.tight_layout()
    plt.show()
except Exception as e:
    print("Plotting skipped:", e)

# ------------- Tips --------------------------
# - Adjust K to explore different cluster granularity (e.g., K=3..10).
# - For auto-discovered clusters, try DBSCAN/HDBSCAN instead of KMeans.
# - To focus on a department, pre-filter `edges` by group name prefix (e.g., GG_Eng_*).
