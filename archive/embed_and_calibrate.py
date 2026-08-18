import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

# ------------------------------
# Configuration
# ------------------------------
INPUT_FILE = "output/labeled_clusters.json"
OUTPUT_FILE = "output/calibration_results.json"

# ------------------------------
# Load the labeled seed data
# ------------------------------
print(" Loading labeled seed data...")
with open(INPUT_FILE, 'r') as f:
    data = json.load(f)

clusters = data['clusters']
print(f" Loaded {len(clusters)} clusters.")

# ------------------------------
# Load MiniLM model
# ------------------------------
print(" Loading MiniLM embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print(" Model loaded.")

# ------------------------------
# Build embedding text (problem + cause + technologies)
# ------------------------------
def get_embedding_text(memory):
    # Following DevMem spec: problem + cause + technologies
    problem = memory.get('problem', '')
    cause = memory.get('cause', '')
    techs = ' '.join(memory.get('technologies', []))
    return f"{problem} {cause} {techs}"

# ------------------------------
# Generate embeddings for all memories
# ------------------------------
print(" Generating embeddings...")
all_memories = []
all_embeddings = []
cluster_labels = []

for cluster_idx, cluster in enumerate(clusters):
    label = cluster['label']
    for mem in cluster['memories']:
        text = get_embedding_text(mem)
        embedding = model.encode(text)
        all_memories.append(mem)
        all_embeddings.append(embedding)
        cluster_labels.append({
            'cluster_id': cluster_idx,
            'label': label,
            'memory_index': len(all_memories) - 1
        })

print(f" Generated {len(all_embeddings)} embeddings (384 dimensions each).")

# ------------------------------
# Compute pairwise cosine similarity
# ------------------------------
print(" Computing pairwise cosine similarities...")
embedding_matrix = np.array(all_embeddings)
similarity_matrix = cosine_similarity(embedding_matrix)

# ------------------------------
# Analyze results by cluster label
# ------------------------------
results = {
    "metadata": {
        "total_memories": len(all_memories),
        "total_clusters": len(clusters),
        "embedding_dimension": 384
    },
    "threshold_analysis": {}
}

# Group by cluster label
label_groups = defaultdict(list)
for item in cluster_labels:
    label_groups[item['label']].append(item['memory_index'])

# For each label type, compute statistics
for label, indices in label_groups.items():
    similarities = []
    for i in range(len(indices)):
        for j in range(i+1, len(indices)):
            sim = similarity_matrix[indices[i]][indices[j]]
            similarities.append(sim)
    
    if similarities:
        avg_sim = np.mean(similarities)
        min_sim = np.min(similarities)
        max_sim = np.max(similarities)
        std_sim = np.std(similarities)
    else:
        avg_sim = min_sim = max_sim = std_sim = 0
    
    results['threshold_analysis'][label] = {
        "count": len(indices),
        "pairwise_similarities": {
            "average": float(avg_sim),
            "min": float(min_sim),
            "max": float(max_sim),
            "std": float(std_sim)
        },
        "all_similarities": [float(s) for s in similarities]
    }

# ------------------------------
# Check thresholds against DevMem spec
# ------------------------------
DUPLICATE_THRESHOLD = 0.90
RELATED_THRESHOLD = 0.75

threshold_check = {
    "duplicate_threshold": DUPLICATE_THRESHOLD,
    "related_threshold": RELATED_THRESHOLD,
    "issues": []
}

# Check duplicate cluster
if 'duplicate' in results['threshold_analysis']:
    dup_data = results['threshold_analysis']['duplicate']
    avg_dup = dup_data['pairwise_similarities']['average']
    min_dup = dup_data['pairwise_similarities']['min']
    
    if avg_dup < DUPLICATE_THRESHOLD:
        threshold_check['issues'].append({
            "label": "duplicate",
            "issue": f"Average similarity ({avg_dup:.3f}) is below threshold {DUPLICATE_THRESHOLD}",
            "recommendation": f"Consider lowering DUPLICATE_THRESHOLD to {avg_dup:.2f} or check cluster quality"
        })
    else:
        threshold_check['issues'].append({
            "label": "duplicate",
            "status": " PASS",
            "message": f"Average similarity ({avg_dup:.3f}) ≥ {DUPLICATE_THRESHOLD}"
        })

# Check related cluster
if 'related' in results['threshold_analysis']:
    rel_data = results['threshold_analysis']['related']
    avg_rel = rel_data['pairwise_similarities']['average']
    min_rel = rel_data['pairwise_similarities']['min']
    
    if avg_rel < RELATED_THRESHOLD:
        threshold_check['issues'].append({
            "label": "related",
            "issue": f"Average similarity ({avg_rel:.3f}) is below threshold {RELATED_THRESHOLD}",
            "recommendation": f"Consider lowering RELATED_THRESHOLD to {avg_rel:.2f}"
        })
    else:
        threshold_check['issues'].append({
            "label": "related",
            "status": " PASS",
            "message": f"Average similarity ({avg_rel:.3f}) ≥ {RELATED_THRESHOLD}"
        })

# Check distinct clusters
distinct_sims = []
if 'distinct' in results['threshold_analysis']:
    dist_data = results['threshold_analysis']['distinct']
    distinct_sims = dist_data['all_similarities']
    
    # Check if any distinct pair is too similar
    too_similar = [sim for sim in distinct_sims if sim >= RELATED_THRESHOLD]
    
    if too_similar:
        threshold_check['issues'].append({
            "label": "distinct",
            "issue": f"{len(too_similar)} distinct pairs have similarity ≥ {RELATED_THRESHOLD}",
            "recommendation": "These memories might actually be related. Review the cluster labels."
        })
    else:
        threshold_check['issues'].append({
            "label": "distinct",
            "status": " PASS",
            "message": f"All distinct pairs have similarity < {RELATED_THRESHOLD}"
        })

results['threshold_check'] = threshold_check

# ------------------------------
# Save results
# ------------------------------
print(f"Saving results to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, 'w') as f:
    json.dump(results, f, indent=2)

# ------------------------------
# Print summary
# ------------------------------
print("\n" + "="*60)
print(" CALIBRATION RESULTS")
print("="*60)

print(f"\n Total memories: {len(all_memories)}")
print(f" Total clusters: {len(clusters)}")

print("\n Threshold Analysis:")
for label, data in results['threshold_analysis'].items():
    sim_data = data['pairwise_similarities']
    print(f"\n  {label.upper()}:")
    print(f"    Count: {data['count']}")
    print(f"    Avg similarity: {sim_data['average']:.4f}")
    print(f"    Min: {sim_data['min']:.4f}, Max: {sim_data['max']:.4f}")

print("\n Threshold Check:")
for issue in threshold_check['issues']:
    if 'status' in issue:
        print(f"  {issue['status']} {issue['label']}: {issue['message']}")
    else:
        print(f"    {issue['label']}: {issue['issue']}")
        print(f"     → {issue.get('recommendation', '')}")

print("\n" + "="*60)
print(" Calibration complete!")
print(f" Full results saved to: {OUTPUT_FILE}")