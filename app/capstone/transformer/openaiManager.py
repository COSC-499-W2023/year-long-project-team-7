from django.conf import settings
from .models import Conversion, File
from typing import List, Dict
import json
import openai

class OpenAiManager:

    def __init__(self, texts: Dict[str, str], conversion: Conversion):
        openai.api_key = settings.OPENAI_API_KEY
        self.conversion = conversion
        self.texts = texts

    
    def prompt(self, model: str, messages: List[Dict[str,str]], temprature: int, max_tokens: int) -> str:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temprature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return "response"