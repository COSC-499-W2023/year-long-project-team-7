from pptx import Presentation  # type: ignore
from pptx.util import Inches  # type: ignore
from .models import Conversion
from django.conf import settings
import json
import openai
import os
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from io import BytesIO
import tiktoken
import re
import random


class PresentationGenerator:
    def __init__(
        self,
        chosen_model: str,
        texts: dict[str, str],
        conversion: Conversion,
        temperature: int,
    ):
        available_models = {
            "gpt-3.5-turbo-0613": 4090
        }  # true value is 4097 but this is lower for saftey

        openai.api_key = settings.OPENAI_API_KEY

        self.temperature = temperature
        self.conversion = conversion
        self.texts = texts
        self.chosen_model = chosen_model
        self.max_tokens = available_models[chosen_model]
        self.language = json.loads(conversion.user_parameters).get("language", "")

        with open("app/capstone/prompts.json", "r") as file:
            self.prompts = json.load(file)

        if self.language != "English":
            self.user_prompt = self.translate(
                json.loads(conversion.user_parameters).get("text_input", ""),
                self.language,
            )
            for key in self.prompts:
                self.prompts[key] = self.translate(self.prompts[key], self.language)
        else:
            self.user_prompt = json.loads(conversion.user_parameters).get(
                "text_input", ""
            )

        self.num_slides = json.loads(conversion.user_parameters).get("length", 3)
        self.complexity = json.loads(conversion.user_parameters).get("complexity", 50)

    def translate(self, text: str, language: str) -> str:
        messages = [
            self.system_message(f"{self.prompts['translate']}{language}"),
            self.user_message(text),
        ]

        return self.prompt(messages)

    def build_presentation(self) -> str:
        file_system = FileSystemStorage()

        template = Presentation(
            file_system.path("template_01.pptx")
        )  # make variable later

        title_slide_layout = template.slide_layouts[0]
        # paragraph_slide_layout = template.slide_layouts[1]
        points_slide_layout = template.slide_layouts[3]
        # image_slide_layout = template.slide_layouts[3]
        # final_slide_layout = template.slide_layouts[4]
        prs = Presentation()

        # Create Title slide
        messages = []
        sys_message = f"{self.prompts['summary']}"
        messages.append(self.system_message(sys_message))

        summaries = self.prompt_with_texts(messages)

        super_summary = (
            self.create_super_summary(summaries) if len(summaries) > 1 else summaries[0]
        )

        title = self.prompt(
            [
                self.system_message(self.prompts["title"]),
                self.user_message(super_summary),
            ]
        )
        sub_title = self.prompt(
            [
                self.system_message(f"{self.prompts['sub-title']}{title}"),
                self.user_message(super_summary),
            ]
        )
        title_slide = prs.slides.add_slide(title_slide_layout)
        title_slide.shapes.title.text = title
        title_slide.shapes[1].text = sub_title

        # Create content slides
        messages = []
        messages.append(self.system_message(self.prompts["section-title"]))
        section_titles = [
            section.strip()
            for section in "\n".join(self.prompt_with_texts(messages))
            .replace("-", "")
            .split("\n")
        ]

        # num_sections = len(section_titles) if len(section_titles) < 5 else 5

        # random_section_titles = [re.sub(r'(\d|\.)','',title).strip() for title in random.sample(section_titles, num_sections)]

        for title in section_titles:
            print(f"Generating slide... title: {title}")
            content_slide = prs.slides.add_slide(points_slide_layout)
            content_slide.shapes.title.text = title

            # messages = []
            # messages.append(self.system_message(f"{self.prompts['points']}{title}"))
            # section_points_arr = [section_points.strip() for section_points in '\n'.join(self.prompt_with_texts(messages)).replace('-', '').split('\n')]

            # num_points = random.randint(3,6)

            # chosen_points = re.sub(r'(\d|\.)','','\n'.join(random.sample(section_points_arr, num_points)))

            # content_slide.shapes[1].text = chosen_points

        buffer = BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"conversion_output_{self.conversion.id}.pptx"

        file_system.save(rel_path, file_content)

        return rel_path

    def create_super_summary(self, summaries: list[str]) -> str:
        return summaries[0]  # fix later

    def count_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0613")
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def count_message_tokens(self, messages: list[dict[str, str]]) -> int:
        num_tokens = 0
        for message in messages:
            num_tokens += 4
            for key, value in message.items():
                num_tokens += self.count_tokens(value)
                if key == "name":
                    num_tokens += -1
        num_tokens += 2
        return num_tokens

    def user_message(self, text: str) -> dict[str, str]:
        return {"role": "user", "content": text}

    def system_message(self, text: str) -> dict[str, str]:
        return {"role": "system", "content": text}

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
    def prompt_with_texts(self, messages: list[dict[str, str]]) -> list[str]:
        responses = []

        prompt_tokens = self.count_message_tokens(messages)

        if prompt_tokens > self.max_tokens // 4:
            responses.append("Error: Prompt too long")
            return responses

        for path, text in self.texts.items():
            text_tokens = self.count_tokens(text)

            total_input_tokens = prompt_tokens + text_tokens

            if total_input_tokens > self.max_tokens * 0.75:
                chunks = self.get_chunks(text, prompt_tokens)

                for chunk in chunks:
                    messages.append(self.user_message(chunk))

                    chunk_response = self.prompt(messages)

                    messages.pop()
                    responses.append(chunk_response)

            else:
                messages.append(self.user_message(text))

                text_response = self.prompt(messages)

                messages.pop()
                responses.append(text_response)

        return responses

    def prompt(self, messages: list[dict[str, str]]) -> str:
        tokens = self.max_tokens - self.count_message_tokens(messages)

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
