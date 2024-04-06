import typing
from openai import OpenAI
from django.conf import settings
from .models import Conversion, File, Exercise
from tenacity import retry, stop_after_attempt, wait_random_exponential
import re
from .prompts import *


class OpenAiManager:
    def __init__(self, model: str) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization="org-hYPJO2WKqFAN1o75AdfdfeBx")  # type: ignore

        self.model = model
        self.messages: list[dict[str, str]] = []

    def set_system_prompt(self, system_prompt: str) -> None:
        self.messages = [{"role": "system", "content": system_prompt}]

    def prompt_chat(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        return self.create_chat()

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_chat(self) -> str:
        return str(
            self.client.chat.completions.create(  # type: ignore
                model=self.model,
                messages=self.messages,
                response_format={"type": "json_object"},
            )
            .choices[0]
            .message.content
        )
