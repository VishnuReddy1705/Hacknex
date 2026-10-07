import os
import requests
from typing import Dict, Any, Optional
from backend.app.config import settings

class VLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.provider = settings.LLM_PROVIDER
        self.is_available = bool(self.api_key and self.api_key.strip())

    def verify_or_synthesize(
        self,
        question: str,
        structured_evidence: Dict[str, Any],
        fallback_answer: str
    ) -> Dict[str, Any]:
        """
        If LLM API key is configured, uses VLM/LLM to refine language and double-check evidence.
        Otherwise, returns deterministic fallback_answer without failing.
        """
        if not self.is_available:
            return {
                "answer": fallback_answer,
                "provider": "deterministic_rule_engine",
                "verified": False,
                "note": "Answer generated deterministically via Temporal Event Graph (no external LLM key required)."
            }

        # Optional LLM call if key provided
        try:
            if self.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                prompt = (
                    f"You are a video intelligence assistant. Based STRICTLY on the following verified temporal evidence from the video, answer the user's question.\n"
                    f"DO NOT hallucinate events. ALWAYS include exact timestamps (MM:SS) in your answer.\n\n"
                    f"Question: {question}\n\n"
                    f"Verified Evidence:\n{structured_evidence}\n\n"
                    f"Draft Answer: {fallback_answer}\n\n"
                    f"Provide a concise, direct answer including the exact timestamps."
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                res = requests.post(url, json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {
                        "answer": text,
                        "provider": f"gemini_{self.model}",
                        "verified": True,
                        "note": "Verified with Vision-Language Model"
                    }
        except Exception as e:
            # Fall back gracefully on network or API failure
            pass

        return {
            "answer": fallback_answer,
            "provider": "deterministic_rule_engine",
            "verified": False,
            "note": "API call failed; returned deterministic temporal graph answer."
        }
