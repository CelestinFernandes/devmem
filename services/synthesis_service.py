# services/synthesis_service.py
import os
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class SynthesisService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        print(" Loading FLAN-T5-base for synthesis...")
        self.model_name = "google/flan-t5-base"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

    def synthesize(self, question: str, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not memories:
            return {"answer": "No relevant learnings found.", "sources": []}

        # Filter out bad memories
        good_memories = []
        for m in memories:
            problem = m.get('problem', '')
            fix = m.get('fix', '')
            if problem and fix and 'Not' not in problem and 'Not' not in fix:
                good_memories.append(m)
        
        if not good_memories:
            good_memories = memories[:2]

        best = good_memories[0]
        
        # Build a simple answer
        answer = (
            f"Based on past experience:\n"
            f"Problem: {best.get('problem', 'an issue')}\n"
            f"Solution: {best.get('fix', 'fix not recorded')}\n"
            f"Lesson: {best.get('lesson', 'lesson not recorded')}"
        )

        return {
            "answer": answer,
            "sources": [
                {"id": m['id'], "title": m['title'], "similarity": m.get('similarity', 0)}
                for m in good_memories[:3]
            ]
        }