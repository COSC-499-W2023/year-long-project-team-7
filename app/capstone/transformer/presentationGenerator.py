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
from openai import OpenAI

GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
GPT_4_1106_PREVIEW = "gpt-4-1106-preview"


class PresentationGenerator:
    def __init__(self, input_file_paths: list[str], conversion: Conversion):
        with open(os.path.join(settings.BASE_DIR, "prompts.json"), "r") as file:
            self.prompts = json.load(file)

        self.conversion = conversion
        self.language = json.loads(conversion.user_parameters).get("language", "")
        self.num_slides = json.loads(conversion.user_parameters).get("length", 3)
        self.complexity = json.loads(conversion.user_parameters).get("complexity", 50)
        self.user_prompt = json.loads(conversion.user_parameters).get("text_input", "")

        openai.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI()

        openai_files = []
        for path in input_file_paths:
            openai_files.append(
                self.client.files.create(file=open(path, "rb"), purpose="assistants")
            )

        self.assistant = self.client.beta.assistants.create(
            instructions=f"{self.prompts['reader']} Only respond in {self.language}",
            tools=[{"type": "retrieval"}],
            model=GPT_4_1106_PREVIEW,
            file_ids=[file.id for file in openai_files],
        )

    def add_message_to_thread(self, thread_id: str, content: str) -> None:
        self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=content
        )

    def prompt_assistant(self, proompt: str) -> str:
        thread = self.client.beta.threads.create()
        self.add_message_to_thread(thread.id, proompt)

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=self.assistant.id
        )

        while run.status != "completed":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run.status == "failed":
                if run.last_error:
                    print(run.last_error.message)
                    return run.last_error.message

        messages = []

        for msg in self.client.beta.threads.messages.list(thread_id=thread.id):
            if msg.role == "assistant":
                content = msg.content[0]
                if hasattr(content, "text"):
                    messages.append(
                        re.sub(r"【.*】", "", content.text.value)
                    )  # Remove source links

        return "\n".join(messages)

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

        title = self.prompt_assistant(self.prompts["title"])
        sub_title = self.prompt_assistant(self.prompts["sub-title"])

        title_slide = prs.slides.add_slide(title_slide_layout)
        title_slide.shapes.title.text = title
        title_slide.shapes[1].text = sub_title

        section_titles = self.prompt_assistant(self.prompts["section-title"]).split(
            "\n"
        )

        for section_title in section_titles:
            content_slide = prs.slides.add_slide(points_slide_layout)
            content_slide.shapes.title.text = section_title
            content_slide.shapes[1].text = self.prompt_assistant(
                f"{self.prompts['points']}{section_title}"
            )

        buffer = BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"conversion_output_{self.conversion.id}.pptx"

        file_system.save(rel_path, file_content)

        return rel_path

    # def count_tokens(self, text: str) -> int:
    #     try:
    #         encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0613")
    #     except KeyError:
    #         encoding = tiktoken.get_encoding("cl100k_base")
    #     return len(encoding.encode(text))

    # def count_message_tokens(self, messages: list[dict[str, str]]) -> int:
    #     num_tokens = 0
    #     for message in messages:
    #         num_tokens += 4
    #         for key, value in message.items():
    #             num_tokens += self.count_tokens(value)
    #             if key == "name":
    #                 num_tokens += -1
    #     num_tokens += 2
    #     return num_tokens

    # def user_message(self, text: str) -> dict[str, str]:
    #     return {"role": "user", "content": text}

    # def system_message(self, text: str) -> dict[str, str]:
    #     return {"role": "system", "content": text}

    # def prompt(self, messages: list[dict[str, str]]) -> str:
    #     tokens = self.max_tokens - self.count_message_tokens(messages)

    #     response = openai.ChatCompletion.create(
    #         model=self.chosen_model,
    #         messages=messages,
    #         temperature=self.temperature,
    #         max_tokens=tokens,
    #         top_p=1,
    #         frequency_penalty=0,
    #         presence_penalty=0,
    #     )

    #     return str(response["choices"][0]["message"]["content"])
