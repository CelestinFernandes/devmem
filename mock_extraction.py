import json
import uuid
from datetime import datetime

def mock_bedrock_extract(raw_text):
    """
    This pretends to be AWS Bedrock Nova Micro.
    It returns a structured memory object from any raw text.
    """
    # A super simple rule-based extraction (just for testing)
    words = raw_text.split()
    
    # Dummy logic to make it look real
    if "pod" in raw_text.lower() or "container" in raw_text.lower():
        problem = "Container crashed due to resource limit"
        cause = "Memory limit set too low"
        fix = "Increase memory limit in deployment.yaml"
        lesson = "Always monitor pod memory usage before setting limits"
        technologies = ["Kubernetes", "Docker"]
        title = "Pod OOMKilled"
    elif "api" in raw_text.lower() or "endpoint" in raw_text.lower():
        problem = "API endpoint returning 500 errors"
        cause = "Database connection pool exhausted"
        fix = "Increase connection pool size and add retry logic"
        lesson = "Monitor connection pool metrics proactively"
        technologies = ["Python", "FastAPI", "PostgreSQL"]
        title = "API timeout issue"
    else:
        problem = raw_text[:50] + "..."
        cause = "Unknown cause (mock)"
        fix = "Investigate further (mock)"
        lesson = "Document the issue properly (mock)"
        technologies = ["General"]
        title = raw_text[:30]
    
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "problem": problem,
        "cause": cause,
        "fix": fix,
        "lesson": lesson,
        "technologies": technologies,
        "confidence": 0.8,
        "needs_review": False,
        "importance": 0.5,
        "created_at": datetime.now().isoformat()
    }

# ---------- TEST IT ----------
if __name__ == "__main__":
    test_text = "My Kubernetes pod got OOMKilled yesterday because memory limit was 512Mi but it needed 1Gi."
    result = mock_bedrock_extract(test_text)
    print(" Mock Extraction Result:")
    print(json.dumps(result, indent=2))
    
    # Now test it with your embedding model
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Build the embedding text (problem + cause + technologies)
    embed_text = result['problem'] + " " + result['cause'] + " " + " ".join(result['technologies'])
    embedding = model.encode(embed_text)
    print(f"\n✅ Embedding generated: {len(embedding)} dimensions")
    print(f"First 5 numbers: {embedding[:5]}")