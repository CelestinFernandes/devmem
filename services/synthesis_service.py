import os
import requests
from typing import List, Dict, Any

class SynthesisService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}

    def synthesize(self, question: str, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not memories:
            return {"answer": "No relevant learnings found.", "sources": []}

        good_memories = []
        for m in memories:
            problem = m.get('problem', '')
            fix = m.get('fix', '')
            if problem and fix and 'Not' not in problem and 'Not' not in fix:
                good_memories.append(m)
        if not good_memories:
            good_memories = memories[:2]

        best = good_memories[0]
        prompt = f"Based on past learning: Problem: {best.get('problem')}, Solution: {best.get('fix')}, Lesson: {best.get('lesson')}. Answer: {question}"

        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": prompt})
            if response.status_code == 200:
                output = response.json()
                answer = output[0]['generated_text']
            else:
                answer = self._fallback_answer(best)
        except:
            answer = self._fallback_answer(best)

        return {
            "answer": answer,
            "sources": [
                {"id": m['id'], "title": m['title'], "similarity": m.get('similarity', 0)}
                for m in good_memories[:3]
            ]
        }

    def _fallback_answer(self, best: Dict) -> str:
        return (
            f"Based on past experience:\n"
            f"Problem: {best.get('problem', 'an issue')}\n"
            f"Solution: {best.get('fix', 'fix not recorded')}\n"
            f"Lesson: {best.get('lesson', 'lesson not recorded')}"
        )