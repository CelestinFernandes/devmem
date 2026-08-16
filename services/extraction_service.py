# services/extraction_service.py
import os
import re
from typing import Dict, Any
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class ExtractionService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        print("🧠 Loading FLAN-T5-large for extraction...")
        self.model_name = "google/flan-t5-large"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

    def extract(self, raw_text: str) -> Dict[str, Any]:
        # Simple prompt that works
        prompt = f"""
Extract problem, cause, fix, lesson from:
{raw_text}

Problem:
Cause:
Fix:
Lesson:
"""
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.model.generate(**inputs, max_new_tokens=150)
        output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Try to parse the output
        result = self._parse_output(output_text, raw_text)
        return self._ensure_fields(result, raw_text)

    def _parse_output(self, text: str, raw_text: str) -> Dict:
        """Parse the model output and fallback to manual extraction"""
        lines = text.split('\n')
        fields = {'problem': '', 'cause': '', 'fix': '', 'lesson': ''}
        current = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if lower.startswith('problem:'):
                current = 'problem'
                fields['problem'] = line.split(':', 1)[-1].strip()
            elif lower.startswith('cause:'):
                current = 'cause'
                fields['cause'] = line.split(':', 1)[-1].strip()
            elif lower.startswith('fix:'):
                current = 'fix'
                fields['fix'] = line.split(':', 1)[-1].strip()
            elif lower.startswith('lesson:'):
                current = 'lesson'
                fields['lesson'] = line.split(':', 1)[-1].strip()
            elif current and line:
                fields[current] += ' ' + line

        # If any field is empty, use manual extraction
        for key in fields:
            if not fields[key] or fields[key].strip() in ['', 'N/A', 'Unknown']:
                fields[key] = self._manual_extract(key, raw_text)

        # Technologies
        tech_keywords = ['kubernetes', 'docker', 'python', 'aws', 'hadoop', 'spark', 'java', 'postgres', 'react', 'node', 'hdfs', 'yarn']
        techs = [t for t in tech_keywords if t.lower() in raw_text.lower()]
        fields['technologies'] = techs
        fields['title'] = raw_text[:100] + ('...' if len(raw_text) > 100 else '')

        return fields

    def _manual_extract(self, field: str, text: str) -> str:
        """Extract specific field using keyword heuristics"""
        sentences = text.split('. ')
        
        if field == 'problem':
            # First 2 sentences
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