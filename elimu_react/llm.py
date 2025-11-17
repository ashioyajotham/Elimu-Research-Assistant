"""
LLM interface with resilient Gemini model fallback logic.
"""

from __future__ import annotations

from typing import Iterable, List, Optional
import re
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions


class LLMInterface:
    """
    Wrapper around Google Gemini models with automatic fallback when a model is
    unavailable (404) or temporarily quota-limited (429/ResourceExhausted).
    """

    def __init__(
        self,
        api_key: str,
        model_candidates: Iterable[str],
        temperature: float = 0.1,
    ) -> None:
        genai.configure(api_key=api_key)
        self.temperature = temperature
        self.candidates: List[str] = list(dict.fromkeys(model_candidates))  # dedupe
        if not self.candidates:
            raise ValueError("At least one Gemini model must be supplied.")

        self.generation_config = {
            "temperature": temperature,
            "top_p": 0.9,
            "top_k": 32,
            "max_output_tokens": 8192,
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self._model = None
        self._active_model_name = None

    # --------------------------------------------------------------------- public API

    def generate(self, prompt: str, retry_per_model: int = 2) -> str:
        last_error: Optional[Exception] = None

        for candidate in self.candidates:
            for attempt in range(retry_per_model):
                try:
                    model = self._ensure_model(candidate)
                    response = model.generate_content(prompt)
                    if not response.text:
                        raise ValueError("Empty response from Gemini model.")
                    return response.text
                except google_exceptions.ResourceExhausted as exc:
                    last_error = exc
                    delay = self._retry_delay(exc, attempt)
                    time.sleep(delay)
                    continue
                except google_exceptions.NotFound as exc:
                    last_error = exc
                    break  # try next candidate
                except Exception as exc:
                    last_error = exc
                    break  # move to next candidate

        if last_error:
            raise last_error
        raise RuntimeError("LLMInterface failed without receiving an exception.")

    # ------------------------------------------------------------------ helpers

    def _ensure_model(self, model_name: str):
        if self._active_model_name == model_name and self._model is not None:
            return self._model

        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )
        self._active_model_name = model_name
        return self._model

    @staticmethod
    def _retry_delay(exc: Exception, attempt_index: int) -> float:
        message = getattr(exc, "message", None) or str(exc)
        match = re.search(r"retry in ([\d\.]+)s", message)
        if match:
            return max(float(match.group(1)), 0.5)
        match = re.search(r"seconds:\s*(\d+)", message)
        if match:
            return max(float(match.group(1)), 1.0)
        return min(2 ** attempt_index, 8.0)

