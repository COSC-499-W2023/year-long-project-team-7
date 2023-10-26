from django.conf import settings
from .models import Conversion, File
from typing import List, Dict
import json
import openai


class OpenAiManager:
    def __init__(
        self, chosen_model: str, texts: Dict[str, str], conversion: Conversion
    ):
        available_models = {"gpt-3.5-turbo": 4096}

        openai.api_key = settings.OPENAI_API_KEY
        self.conversion = conversion
        self.texts = texts
        self.chosen_model = chosen_model
        self.max_tokens = available_models[chosen_model]
        self.messages = []

        user_parameters_dict = json.loads(conversion.user_parameters)
        user_prompt = user_parameters_dict.get("text_input", "")

        combined_text = " ".join(texts.values())

        combined_text = user_prompt + " " + combined_text

        words = combined_text.split()
        for i in range(0, len(words), 500):
            chunk = " ".join(words[i : i + 500])

            self.messages.append({"role": "user", "content": chunk})

    def prompt(self, temprature: int) -> str:
        response = openai.ChatCompletion.create(
            model=self.chosen_model,
            messages=self.messages,
            temperature=temprature,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        print(response)
        return str(response["choices"][0]["message"]["content"])
