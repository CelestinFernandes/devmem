import os
import requests
import re
from typing import Dict, Any

class ExtractionService:
    def __init__(self, use_bedrock=False, region=None):
        self.use_bedrock = use_bedrock
        self.api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN', '')}"}

    def extract(self, raw_text: str) -> Dict[str, Any]:
        prompt = f"Extract problem, cause, fix, lesson from: {raw_text}"
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": prompt})
            if response.status_code == 200:
                output = response.json()
                output_text = output[0]['generated_text']
                result = self._parse_output(output_text, raw_text)
            else:
                result = {'problem': self._manual_extract('problem', raw_text)}
        except:
            result = {'problem': self._manual_extract('problem', raw_text)}
        return self._ensure_fields(result, raw_text)

    def _parse_output(self, text: str, raw_text: str) -> Dict:
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

        for key in fields:
            if not fields[key] or fields[key].strip() in ['', 'N/A', 'Unknown']:
                fields[key] = self._manual_extract(key, raw_text)

        tech_keywords = ['kubernetes', 'docker', 'python', 'aws', 'hadoop', 'spark', 'java', 'postgres', 'react', 'node', 'hdfs', 'yarn']
        techs = [t for t in tech_keywords if t.lower() in raw_text.lower()]
        fields['technologies'] = techs
        fields['title'] = raw_text[:100] + ('...' if len(raw_text) > 100 else '')
        return fields

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