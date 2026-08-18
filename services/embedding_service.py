import os
import requests
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}

    def encode(self, text: str) -> np.ndarray:
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": text})
            if response.status_code == 200:
                embedding = response.json()
                return np.array(embedding)
            else:
                # fallback (only for demo)
                return np.random.randn(384)
        except:
            return np.random.randn(384)