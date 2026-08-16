import json
import pandas as pd
from datasets import load_dataset

# Load the dataset from Hugging Face
print("Loading GitHub Issues dataset...")
dataset = load_dataset("sharjeelyunus/github-issues-dataset", split="train")

# Sample a subset (use more for better results)
sample_size = 2000
sampled = dataset.shuffle(seed=42).select(range(min(sample_size, len(dataset))))

training_data = []

for item in sampled:
    title = item.get('title', '')
    body = item.get('body', '') or ''
    labels = item.get('labels', [])
    
    # Skip if no useful content
    if len(title) < 10:
        continue
    
    # Build the input text
    input_text = f"Title: {title}\nDescription: {body}"
    
    # The output format your model needs to learn
    # For now, we use a simple heuristic - you'll improve this
    output = {
        "problem": title[:100] if len(title) > 100 else title,
        "cause": "Extract cause from description" if body else "Unknown",
        "fix": "Extract fix from description" if body else "Unknown",
        "lesson": "Key lesson from this issue" if body else "Unknown",
        "technologies": [label for label in labels if isinstance(label, str)][:3]
    }
    
    training_data.append({
        "input": input_text,
        "output": json.dumps(output)
    })

# Save to file
with open('training_data.json', 'w') as f:
    json.dump(training_data, f, indent=2)

print(f"✅ Created {len(training_data)} training examples")
print("Saved to training_data.json")