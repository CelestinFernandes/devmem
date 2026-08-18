import os
import json
import requests
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Gemini endpoint — only this URL changes from FLAN-T5
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"


class ExtractionService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        # HF endpoint kept so nothing else breaks if it's referenced externally,
        # but we no longer call it for generation.
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}

    # ------------------------------------------------------------------
    # Load the extraction prompt template from the prompts directory.
    # Falls back to an inline template if the file is missing.
    # ------------------------------------------------------------------
    def _build_prompt(self, raw_text: str) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', 'prompts', 'extract_memory.md'
        )
        try:
            with open(os.path.normpath(prompt_path), 'r', encoding='utf-8') as f:
                template = f.read()
            return template.replace('{text}', raw_text)
        except Exception:
            # Inline fallback — mirrors the content of prompts/extract_memory.md
            return (
                "Extract the following information from this engineering learning text:\n\n"
                "1. problem: What was the issue? (short, max 100 words)\n"
                "2. cause: Why did it happen? (short, max 100 words)\n"
                "3. fix: How was it resolved? (short, max 100 words)\n"
                "4. lesson: What was learned? (short, max 100 words)\n"
                "5. technologies: List of technologies mentioned (as a JSON array of strings)\n\n"
                "Return ONLY valid JSON with these fields. Do not include any other text.\n\n"
                f"Text:\n{raw_text}"
            )

    def extract(self, raw_text: str) -> Dict[str, Any]:
        result = self._gemini_extract(raw_text)
        return self._ensure_fields(result, raw_text)

    # ------------------------------------------------------------------
    # Gemini extraction — replaces the FLAN-T5 call.
    # On ANY failure falls back to manual extraction, preserving old behaviour.
    # ------------------------------------------------------------------
    def _gemini_extract(self, raw_text: str) -> Dict[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("EXTRACTION: No GEMINI_API_KEY found. Using manual fallback.")
            return self._manual_fallback_dict(raw_text)

        prompt = self._build_prompt(raw_text)
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
                logger.warning(f"EXTRACTION: Gemini returned status {response.status_code}. Using manual fallback.")
                return self._manual_fallback_dict(raw_text)

            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]

            # Strip markdown code fences if Gemini wraps JSON in ```json ... ```
            text = re.sub(r'^```[a-zA-Z]*\s*', '', text.strip())
            text = re.sub(r'\s*```$', '', text.strip())

            parsed = json.loads(text)
            # Normalise technologies to a list
            if "technologies" not in parsed or not isinstance(parsed["technologies"], list):
                parsed["technologies"] = []
            
            logger.info("EXTRACTION: Successfully extracted via Gemini.")
            return parsed

        except Exception as e:
            logger.warning(f"EXTRACTION: Gemini call failed with exception: {type(e).__name__}: {str(e)}. Using manual fallback.")
            return self._manual_fallback_dict(raw_text)

    # ------------------------------------------------------------------
    # Builds a dict using the existing manual extraction helpers so the
    # fallback path produces the same shape as before.
    # ------------------------------------------------------------------
    def _manual_fallback_dict(self, raw_text: str) -> Dict[str, Any]:
        tech_keywords = [
            'kubernetes', 'docker', 'python', 'aws', 'hadoop', 'spark',
            'java', 'postgres', 'react', 'node', 'hdfs', 'yarn'
        ]
        techs = [t for t in tech_keywords if t.lower() in raw_text.lower()]
        return {
            'problem':      self._manual_extract('problem', raw_text),
            'cause':        self._manual_extract('cause', raw_text),
            'fix':          self._manual_extract('fix', raw_text),
            'lesson':       self._manual_extract('lesson', raw_text),
            'technologies': techs,
            'title':        raw_text[:100] + ('...' if len(raw_text) > 100 else ''),
        }

    # ------------------------------------------------------------------
    # Unchanged helpers from original implementation
    # ------------------------------------------------------------------
    def _manual_extract(self, field: str, text: str) -> str:
        sentences = text.split('. ')
        if field == 'problem':
            return '. '.join(sentences[:2]) if sentences else text[:100]
        elif field == 'cause':
            keywords = ['because', 'due to', 'since', 'caused by', 'led to', 'reason']
            for sent in sentences:
                if any(kw in sent.lower() for kw in keywords):
                    return sent
            return "Not specified in the text."
        elif field == 'fix':
            keywords = ['fix', 'solution', 'increase', 'decrease', 'change', 'add', 'remove', 'implement', 'use']
            for sent in sentences:
                if any(kw in sent.lower() for kw in keywords):
                    return sent
            return "Not specified in the text."
        elif field == 'lesson':
            keywords = ['learn', 'lesson', 'always', 'never', 'remember', 'ensure', 'consider']
            for sent in sentences:
                if any(kw in sent.lower() for kw in keywords):
                    return sent
            return "Keep this learning for future reference."
        return text

    def _ensure_fields(self, result: Dict, raw_text: str) -> Dict:
        required = ['title', 'problem', 'cause', 'fix', 'lesson', 'technologies']
        for field in required:
            if field not in result or not result[field] or result[field] in ["Unknown", "Not extracted", "", "None"]:
                if field == 'title':
                    result[field] = raw_text[:100] + ('...' if len(raw_text) > 100 else '')
                elif field == 'technologies':
                    result[field] = []
                elif field == 'problem':
                    result[field] = raw_text[:200]
                elif field == 'cause':
                    result[field] = "Not clearly stated."
                elif field == 'fix':
                    result[field] = "Not clearly stated."
                elif field == 'lesson':
                    result[field] = "Document this learning."
        return result
