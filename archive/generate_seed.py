import pandas as pd
import json
import os
import random
from datetime import datetime
from difflib import SequenceMatcher

# ------------------------------
# Configuration
# ------------------------------
DATA_DIR = "data"
OUTPUT_DIR = "output"
CSV_FILE = os.path.join(DATA_DIR, "jira_apache_hadoophdfs_labeled.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "labeled_clusters.json")
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ------------------------------
# Helper: text similarity
# ------------------------------
def text_similarity(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

# ------------------------------
# Load and sample data
# ------------------------------
def load_and_sample(csv_path, n=60):
    print(f" Loading data from {csv_path} ...")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='latin-1')
    print(f"    Loaded {len(df)} records.")

    # Keep only rows with non‑empty summary or description
    df = df[df['summary'].notna() | df['description'].notna()].copy()
    print(f"    Filtered to {len(df)} with text.")

    # We don't have Status/Resolution, so just sample randomly
    # but we can prioritise longer descriptions (more information)
    df['text_len'] = df['description'].fillna('').apply(len)
    df = df.sort_values('text_len', ascending=False)
    sampled = df.head(n).sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"    Sampled {len(sampled)} records (prioritising longer descriptions).")
    return sampled

# ------------------------------
# Convert one row to a DevMeM memory
# ------------------------------
def row_to_memory(row):
    summary = str(row.get('summary', ''))[:200]
    description = str(row.get('description', ''))[:500]

    # Placeholder extraction (later replace with Bedrock)
    problem = f"Issue: {summary}"
    cause = "Needs analysis (placeholder)."
    fix = "Refer to comments or patches (placeholder)."
    lesson = f"Type: {row.get('type', 'bug')} (placeholder)."

    # Guess technologies from text
    tech_keywords = ['Hadoop', 'hdfs', 'mapreduce', 'yarn', 'java', 'spark', 'hive', 'pig', 'zookeeper', 'maven', 'jdk']
    combined = (summary + " " + description).lower()
    technologies = [t for t in tech_keywords if t in combined]
    if not technologies:
        technologies = ["Hadoop"]

    return {
        "title": summary,
        "problem": problem,
        "cause": cause,
        "fix": fix,
        "lesson": lesson,
        "technologies": technologies,
        "importance": random.randint(1, 5),
        "confidence": 0.8,
        "needs_review": False
    }

# ------------------------------
# Build clusters (duplicate, related, distinct)
# ------------------------------
def build_clusters(memories):
    clusters = []

    # 1. DUPLICATE: find two with high summary similarity (> 0.8)
    used = set()
    duplicate_pair = None
    for i in range(len(memories)):
        for j in range(i+1, len(memories)):
            sim = text_similarity(memories[i]['title'], memories[j]['title'])
            if sim > 0.8:
                duplicate_pair = (i, j)
                break
        if duplicate_pair:
            break

    if duplicate_pair:
        i, j = duplicate_pair
        clusters.append({
            "label": "duplicate",
            "memories": [memories[i], memories[j]],
            "description": "These two bug reports have very similar summaries (title similarity > 0.8)."
        })
        used.update([i, j])
    else:
        # fallback: take first two
        clusters.append({
            "label": "duplicate",
            "memories": memories[:2],
            "description": "First two reports (artificially labeled as duplicate)."
        })
        used.update([0, 1])

    # 2. RELATED: pick a group that shares at least one technology
    related_indices = []
    for idx, mem in enumerate(memories):
        if idx in used: continue
        tech_set = set(mem['technologies'])
        for jdx, mem2 in enumerate(memories):
            if jdx in used or jdx <= idx: continue
            if set(mem2['technologies']) & tech_set:
                related_indices = [idx, jdx]
                # add a third (any other not used)
                for k, _ in enumerate(memories):
                    if k not in used and k not in related_indices:
                        related_indices.append(k)
                        break
                break
        if related_indices:
            break

    if related_indices:
        clusters.append({
            "label": "related",
            "memories": [memories[idx] for idx in related_indices],
            "description": "These reports are about related topics (shared technologies)."
        })
        used.update(related_indices)
    else:
        # fallback: pick the next 3 unused
        fallback = [idx for idx in range(len(memories)) if idx not in used][:3]
        if len(fallback) >= 2:
            clusters.append({
                "label": "related",
                "memories": [memories[idx] for idx in fallback],
                "description": "Artificially labeled related."
            })
            used.update(fallback)

    # 3. DISTINCT: group remaining into small clusters (2-3 each)
    remaining = [idx for idx in range(len(memories)) if idx not in used]
    random.shuffle(remaining)
    group_size = 3
    for i in range(0, len(remaining), group_size):
        group = remaining[i:i+group_size]
        if len(group) >= 2:
            clusters.append({
                "label": "distinct",
                "memories": [memories[idx] for idx in group],
                "description": f"These reports are unrelated to each other (Group {i//group_size + 1})."
            })
            used.update(group)
        else:
            # add leftovers to the last distinct cluster
            if clusters and clusters[-1]['label'] == 'distinct':
                clusters[-1]['memories'].extend([memories[idx] for idx in group])
                used.update(group)

    return clusters

# ------------------------------
# Main
# ------------------------------
def main():
    print("\n DevMeM Seed Data Generator")
    print("==============================")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load & sample
    df = load_and_sample(CSV_FILE, n=80)
    if df is None or df.empty:
        print(" No data loaded. Check your CSV file path.")
        return

    # 2. Convert to memories
    print("🔄 Converting rows to memories...")
    memories = [row_to_memory(row) for _, row in df.iterrows()]
    print(f"    Generated {len(memories)} memory objects.")

    # 3. Build clusters
    print(" Building clusters (duplicate, related, distinct)...")
    clusters = build_clusters(memories)

    # 4. Assemble final JSON
    final = {
        "metadata": {
            "version": "1.0",
            "description": "Labeled seed dataset for DevMeM similarity threshold calibration.",
            "created_at": datetime.now().isoformat(),
            "source": "Hadoop bug reports (Kaggle-style with pk, summary, description, type).",
            "total_memories": len(memories),
            "total_clusters": len(clusters)
        },
        "clusters": clusters
    }

    # 5. Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final, f, indent=2)

    print(f"\n Done! Saved to: {OUTPUT_FILE}")
    print(f"   - Total memories: {len(memories)}")
    print(f"   - Total clusters: {len(clusters)}")
    print("   - Cluster breakdown:")
    for c in clusters:
        print(f"       {c['label']}: {len(c['memories'])} memories")

if __name__ == "__main__":
    main()