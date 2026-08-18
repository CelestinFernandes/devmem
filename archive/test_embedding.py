from sentence_transformers import SentenceTransformer

print("Loading the AI model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Test it with a dummy sentence
text = "My Kubernetes pod crashed because of memory limits"
embedding = model.encode(text)

print(f" AI Model works! Your embedding has {len(embedding)} numbers (dimensions).")
print(f"First 5 numbers: {embedding[:5]}")