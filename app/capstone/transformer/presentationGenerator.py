from time import sleep
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
import requests
from .models import File
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor


GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
GPT_4_1106_PREVIEW = "gpt-4-1106-preview"


class PresentationGenerator:
    def __init__(self, input_file_paths: list[str], conversion: Conversion):
        with open(os.path.join(settings.BASE_DIR, "prompts.json"), "r") as file:
            self.prompts = json.load(file)

        self.conversion = conversion
        self.user_prompt = json.loads(conversion.user_parameters).get("prompt", "")
        self.language = json.loads(conversion.user_parameters).get("language", "")
        self.tone = json.loads(conversion.user_parameters).get("tone", "")
        self.complexity = json.loads(conversion.user_parameters).get("complexity", 3)
        self.num_slides = json.loads(conversion.user_parameters).get("num_slides", 10)
        self.image_frequency = json.loads(conversion.user_parameters).get(
            "image_frequency", 3
        )
        self.template = json.loads(conversion.user_parameters).get("template", 1)

        openai.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI()

        openai_files = []
        for path in input_file_paths:
            openai_files.append(
                self.client.files.create(file=open(path, "rb"), purpose="assistants")
            )

        instructions = f"{self.prompts['reader']}"

        instructions = (
            instructions
            if self.language == "Auto"
            else f"{instructions} Only respond in {self.language}"
        )

        instructions = (
            instructions
            if self.tone == "Auto"
            else f"{instructions} {self.prompts['tone'].format(tone=self.tone)}"
        )

        instructions = (
            instructions
            if self.complexity == 3
            else f"{instructions} {self.prompts['complexity'].format(complexity=self.complexity)}"
        )

        instructions = (
            instructions
            if len(self.user_prompt) == 0 or self.user_prompt == ""
            else f"{instructions} {self.prompts['prompt-input'].format(prompt=self.user_prompt)}"
        )

        self.assistant = self.client.beta.assistants.create(
            instructions=instructions,
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

    def image_search(self, search_term: str) -> File:  # This is currently broken
        # api_url = "https://api.search.brave.com/res/v1/images/search"
        # params = {
        #     "q": str(search_term),
        #     "safesearch": "strict",
        #     "count": str(20),
        #     "search_lang": "en",
        #     "country": "us",
        #     "spellcheck": str(1),
        # }

        # headers = {
        #     "Accept": "application/json",
        #     "Accept-Encoding": "gzip",
        #     "X-Subscription-Token": str(settings.BRAVE_SEARCH_API_KEY),
        # }

        # response = None

        # while not response:
        #     try:
        #         response = requests.get(api_url, params=params, headers=headers)
        #         response.raise_for_status()
        #     except Exception as e:
        #         sleep(10)
        #         print(f"An error occurred: {e}. Retrying...")

        # images = response.json().get("results", [])
        # images = [img.get("properties").get("url") for img in images]
        # file_system = FileSystemStorage()

        # image_response = None
        # while not image_response:
        #     try:
        #         image = random.choice(images)
        #         image_response = requests.get(image)
        #         image_response.raise_for_status()
        #     except Exception as e:
        #         sleep(10)
        #         print(f"An error occurred: {e}. Retrying...")

        # image_file = BytesIO(image_response.content)
        # image_file.name = f"{search_term}_{self.conversion.id}.jpg"

        # file_system.save(image_file.name, image_file)

        # found_image = File.objects.create(
        #     date=timezone.now(),
        #     user=None,
        #     conversion=self.conversion,
        #     is_output=False,
        #     type="image",
        #     file=image_file.name,
        # )

        # return found_image
        return File()

    def build_slide(
        self, prs: Presentation, template: Presentation, slide_num: int
    ) -> Presentation:
        image_slide_likelihood = {0: 0, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.6, 5: 0.7, 6: 0.8}

        if slide_num == 1:
            layout = template.slide_layouts.get_by_name("TITLE")
            title_slide = prs.slides.add_slide(layout)

            title = self.prompt_assistant(self.prompts["title"])
            sub_title = self.prompt_assistant(f"{self.prompts['sub-title']}{title}")

            title_slide.shapes.title.text = title
            title_slide.shapes[1].text = sub_title
            return prs

        # if random.random() < image_slide_likelihood.get(self.image_frequency, 0.3):
        #     layout = template.slide_layouts.get_by_name("IMAGE")
        #     image_slide = prs.slides.add_slide(layout)

        #     slide_content = self.prompt_assistant(f"{self.prompts['slide'].format(slide_num=slide_num, num_slides=self.num_slides)}")
        #     slide_title = slide_content.split("\n")[0]
        #     image_slide.shapes.title.text = slide_title
        #     image_slide.shapes[1].text = slide_content

        #     image = self.image_search(self.prompt_assistant(f"{self.prompts['image-search'].format(text=slide_content)}"))

        #     file_system = FileSystemStorage()

        #     image_slide.placeholders[1].insert_picture(file_system.path(image.file.name))

        #     return prs
        selected_content_slide = 1 if random.random() < 0.5 else 2
        layout = template.slide_layouts.get_by_name(f"CONTENT{selected_content_slide}")
        content_slide = prs.slides.add_slide(layout)

        slide_content = self.prompt_assistant(
            f"{self.prompts['slide'].format(slide_num=slide_num, num_slides=self.num_slides)}"
        )
        slide_title = slide_content.split("\n")[0]
        slide_content = slide_content.replace(slide_title, "")
        content_slide.shapes.title.text = slide_title
        content_slide.shapes[1].text = slide_content

        return prs

    def build_presentation(self) -> str:
        file_system = FileSystemStorage()

        template = Presentation(file_system.path(f"template_{self.template}.pptx"))

        prs = Presentation()

        for slide_num in range(1, self.num_slides + 1):
            prs = self.build_slide(prs, template, slide_num)

        # with ThreadPoolExecutor() as executor:
        #     futures = [executor.submit(lambda slide: self.build_slide(prs, template, slide), slide_num)
        #             for slide_num in range(1, self.num_slides + 1)]

        #     for future in futures:
        #         prs = future.result()

        buffer = BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"conversion_output_{self.conversion.id}.pptx"

        file_system.save(rel_path, file_content)

        return rel_path
