from pptx import Presentation  # type: ignore
from pptx.util import Inches  # type: ignore
from .models import Conversion
from typing import List, Dict
from django.conf import settings
import json
import openai
import os
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from io import BytesIO


class PresentationGenerator:
    def __init__(
        self,
        chosen_model: str,
        texts: Dict[str, str],
        conversion: Conversion,
        temperature: int,
    ):
        available_models = {"gpt-3.5-turbo": 4096, "gpt-4": 8191}

        openai.api_key = settings.OPENAI_API_KEY

        self.temperature = temperature
        self.conversion = conversion
        self.texts = texts
        self.chosen_model = chosen_model
        self.max_tokens = available_models[chosen_model]
        self.user_prompt = json.loads(conversion.user_parameters).get("text_input", "")
        self.language = json.loads(conversion.user_parameters).get("language", "")

        with open("app/capstone/prompts.json", "r") as file:
            self.prompts = json.load(file)

    def build_presentation(self) -> str:
        prs = Presentation()
        slide_layout = prs.slide_layouts[1]
        layouts = prs.slide_layouts

        messages = []

        # messages.append(self.user_message(self.prompts['markdown']))
        # messages.append(self.user_message(self.prompts['summary']))
        # messages.append(self.user_message(self.user_prompt))
        messages.append(self.user_message(self.prompts["slides"]))
        messages.append(self.user_message(f"Respond in {self.language}"))

        responses = self.prompt_with_text(messages)

        for response in responses:
            split_for_slides = response.split("\n\n")
            for new_slide_content in split_for_slides:
                title_text = new_slide_content.split("\n")[0]
                new_slide_content = new_slide_content.replace(title_text, "")
                slide = prs.slides.add_slide(slide_layout)
                title = slide.shapes.title
                content = slide.placeholders[1]
                title.text = title_text
                content.text = new_slide_content
                title.top = 0

        buffer = BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"conversion_output_{self.conversion.id}.pptx"

        fs = FileSystemStorage()
        fs.save(rel_path, file_content)

        return rel_path

    def count_tokens(self, text: str) -> int:
        return len(text) // 4 + int(
            len(text) * 0.05
        )  # this is temporary we need to find a better way to limit tokens

    def user_message(self, text: str) -> dict[str, str]:
        return {"role": "user", "content": text}

    def get_chunks(self, text: str, prompt_tokens: int) -> list[str]:
        chunks = []
        max_chunk_tokens = int(self.max_tokens * 0.75) - prompt_tokens

        words = text.split()
        current_chunk = ""

        for word in words:
            word_tokens = self.count_tokens(word)
            if self.count_tokens(current_chunk) + word_tokens <= max_chunk_tokens:
                current_chunk += word + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = word + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    # messages + completion =< max tokens
    # prompts + file content =< messages
    # prompts + file + completion = max tokens
    def prompt_with_text(self, messages: List[dict[str, str]]) -> List[str]:
        responses = []

        prompt_tokens = self.count_tokens(
            " ".join([msg["content"] for msg in messages])
        )

        if prompt_tokens > self.max_tokens // 4:
            responses.append("Error: Prompt too long")
            return responses

        for path, text in self.texts.items():
            text_tokens = self.count_tokens(text)

            total_input_tokens = prompt_tokens + text_tokens

            if total_input_tokens > self.max_tokens * 0.75:
                chunks = self.get_chunks(text, prompt_tokens)

                for chunk in chunks:
                    available_tokens = (
                        self.max_tokens - prompt_tokens - self.count_tokens(chunk)
                    )
                    messages.append(self.user_message(chunk))

                    chunk_response = self.prompt(messages, available_tokens)

                    messages.pop()
                    responses.append(chunk_response)

            else:
                messages.append(self.user_message(text))

                text_response = self.prompt(
                    messages, self.max_tokens - prompt_tokens - text_tokens
                )

                messages.pop()
                responses.append(text_response)

        return responses

    def prompt(self, messages: list[dict[str, str]], tokens: int) -> str:
        response = openai.ChatCompletion.create(
            model=self.chosen_model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        return str(response["choices"][0]["message"]["content"])
