import os
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Gemini endpoint — only this URL changes from FLAN-T5
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"


class SynthesisService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        # HF endpoint kept so nothing else breaks if it's referenced externally,
        # but we no longer call it for generation.
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}

    # ------------------------------------------------------------------
    # Load the synthesis prompt template from the prompts directory.
    # Falls back to an inline template if the file is missing.
    # ------------------------------------------------------------------
    def _build_prompt(self, question: str, good_memories: List[Dict[str, Any]]) -> str:
        context_parts = []
        for i, m in enumerate(good_memories[:3], 1):
            context_parts.append(
                f"Memory {i}:\n"
                f"  Problem: {m.get('problem', '')}\n"
                f"  Fix: {m.get('fix', '')}\n"
                f"  Lesson: {m.get('lesson', '')}"
            )
        context = "\n\n".join(context_parts)

        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', 'prompts', 'ask_ai.md'
        )
        try:
            with open(os.path.normpath(prompt_path), 'r', encoding='utf-8') as f:
                template = f.read()
            return template.replace('{context}', context).replace('{question}', question)
        except Exception:
            # Inline fallback — mirrors ask_ai.md
            return (
                "You are a technical assistant. Given the following past learnings "
                "(each with problem, fix, lesson), answer the user's question.\n\n"
                f"Past learnings:\n{context}\n\n"
                f"User question: {question}\n\n"
                "Provide a concise, helpful answer. Cite which memory (by number) you used. "
                "Format: \"According to Memory 1...\" etc."
            )

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
        prompt = self._build_prompt(question, good_memories)

        answer = self._gemini_synthesize(prompt, best)

        return {
            "answer": answer,
            "sources": [
                {"id": m['id'], "title": m['title'], "similarity": m.get('similarity', 0)}
                for m in good_memories[:3]
            ]
        }

    # ------------------------------------------------------------------
    # Gemini synthesis — replaces the FLAN-T5 call.
    # On ANY failure falls back to _fallback_answer, preserving old behaviour.
    # ------------------------------------------------------------------
    def _gemini_synthesize(self, prompt: str, best: Dict) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("SYNTHESIS: No GEMINI_API_KEY found. Using fallback answer.")
            return self._fallback_answer(best)

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        try:
            response = requests.post(
                GEMINI_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code != 200:
                logger.warning(f"SYNTHESIS: Gemini returned status {response.status_code}. Using fallback answer.")
                return self._fallback_answer(best)

            data = response.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info("SYNTHESIS: Successfully synthesized via Gemini.")
            return answer

        except Exception as e:
            logger.warning(f"SYNTHESIS: Gemini call failed with exception: {type(e).__name__}: {str(e)}. Using fallback answer.")
            return self._fallback_answer(best)

    # ------------------------------------------------------------------
    # Unchanged fallback from original implementation
    # ------------------------------------------------------------------
    def _fallback_answer(self, best: Dict) -> str:
        return (
            f"Based on past experience:\n"
            f"Problem: {best.get('problem', 'an issue')}\n"
            f"Solution: {best.get('fix', 'fix not recorded')}\n"
            f"Lesson: {best.get('lesson', 'lesson not recorded')}"
        )
