from pptx import Presentation  # type: ignore
from .models import Conversion
from django.conf import settings
import json
import os
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from io import BytesIO
import re
import random
from openai import OpenAI
import requests
from .models import File
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_random_exponential


class SlideContent:
    def __init__(
        self,
        slide_num: int,
        slide_type: str,
        title: str,
        sub_title: str,
        image: File,
        points: str,
    ):
        self.slide_type = slide_type
        self.title = title
        self.sub_title = sub_title
        self.image = image
        self.points = points
        self.slide_num = slide_num


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

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)  # type: ignore

        self.openai_files = []
        for path in input_file_paths:
            self.openai_files.append(
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
            model=settings.OPENAI_MODEL,  # type: ignore
            file_ids=[file.id for file in self.openai_files],
        )

    def prompt_assistant(self, proompt: str) -> str:
        thread = self.create_thread()
        self.add_message_to_thread(thread.id, proompt)
        run = self.create_run(thread.id)

        while run.status != "completed":
            run = self.retrieve_run(thread.id, run.id)
            if run.status == "failed":
                if run.last_error:
                    print(run.last_error.message)
                    return str(run.last_error.message)

        messages = []

        for msg in self.list_messages(thread.id):
            if msg.role == "assistant":
                content = msg.content[0]
                if hasattr(content, "text"):
                    messages.append(
                        re.sub(r"【.*】", "", content.text.value)
                    )  # Remove source links

        self.delete_thread(thread.id)
        return "\n".join(messages)

    def image_search(self, query: str) -> File:
        api_url = "https://api.unsplash.com/search/photos"
        params = {"query": query, "client_id": settings.UNSPLASH_ACCESS_KEY}  # type: ignore

        response = requests.get(api_url, params=params).json()

        images = response["results"]
        image_url = images[random.randint(0, len(images) - 1)]["urls"]["raw"]

        image = requests.get(image_url).content

        file_system = FileSystemStorage()
        rel_path = f"{query}.jpg"
        file_system.save(rel_path, ContentFile(image))

        image_file = File(
            user=self.conversion.user,
            conversion=self.conversion,
            type=".jpg",
            file=rel_path,
            is_output=False,
        )

        image_file.save()
        return image_file

    def build_slide(self, slide_num: int) -> SlideContent:
        image_slide_likelihood = {0: 0, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.6, 5: 0.7, 6: 0.8}

        is_image_slide = random.random() < image_slide_likelihood[self.image_frequency]

        if slide_num == 1:
            title = self.prompt_assistant(self.prompts["title"])
            sub_title = self.prompt_assistant(f"{self.prompts['sub-title']}{title}")

            return SlideContent(slide_num, "TITLE", title, sub_title, File(), "None")

        elif is_image_slide:
            query = self.prompt_assistant(self.prompts["image-search"])
            image = self.image_search(query)
            return SlideContent(slide_num, "IMAGE", query, "None", image, "None")

        else:
            slide_content = self.prompt_assistant(
                f"{self.prompts['slide'].format(slide_num=slide_num, num_slides=self.num_slides)}"
            )

            slide_title = slide_content.split("\n")[0]
            slide_points = slide_content.replace(slide_title, "")

            return SlideContent(
                slide_num, "CONTENT", slide_title, "None", File(), slide_points
            )

    def add_slide_to_presentation(
        self, content: SlideContent, template: Presentation
    ) -> None:
        if content.slide_type == "TITLE":
            layout = template.slide_layouts.get_by_name("TITLE")
            title_slide = template.slides.add_slide(layout)
            title_slide.shapes.title.text = content.title
            title_slide.shapes[1].text = content.sub_title

        elif content.slide_type == "CONTENT":
            selected_content_slide = 1 if random.random() < 0.5 else 2
            layout = template.slide_layouts.get_by_name(
                f"CONTENT{selected_content_slide}"
            )
            content_slide = template.slides.add_slide(layout)
            content_slide.shapes.title.text = content.title
            content_slide.shapes[1].text = content.points

        elif content.slide_type == "IMAGE":
            selected_image_slide = 1 if random.random() < 0.5 else 2
            layout = template.slide_layouts.get_by_name(f"IMAGE{selected_image_slide}")
            image_slide = template.slides.add_slide(layout)
            image_slide.shapes.title.text = content.title
            image_slide.shapes[1].insert_picture(content.image.file)

    def build_presentation(self) -> str:
        file_system = FileSystemStorage()

        template = Presentation(file_system.path(f"template_{self.template}.pptx"))

        slide_contents = []

        # Fetch slide content in parallel for speed
        with ThreadPoolExecutor() as executor:
            future_slides = executor.map(
                self.build_slide, range(1, self.num_slides + 1)
            )
            slide_contents = list(future_slides)

        # Sort and add slides to presentation
        sorted_slide_contents = sorted(
            slide_contents, key=lambda slide: slide.slide_num
        )

        for content in sorted_slide_contents:
            self.add_slide_to_presentation(content, template)

        buffer = BytesIO()
        template.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"conversion_output_{self.conversion.id}.pptx"

        file_system.save(rel_path, file_content)

        return rel_path

    # delete all files and assistants when PresentationGenerator object is deleted
    def __del__(self) -> None:
        for file in self.openai_files:
            self.delete_file(file.id)

        self.delete_assistant(self.assistant.id)

    # REQUESTS WITH EXPONENTIAL BACKOFF
    # All requests need to be done like this to deal with rate-limiting
    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def add_message_to_thread(self, thread_id: str, content: str) -> None:
        self.client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=content
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_thread(self):  # type: ignore
        return self.client.beta.threads.create()

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def create_run(self, thread_id: str):  # type: ignore
        return self.client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=self.assistant.id
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def retrieve_run(self, thread_id: str, run_id: str):  # type: ignore
        return self.client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_messages(self, thread_id: str):  # type: ignore
        return self.client.beta.threads.messages.list(thread_id=thread_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_thread(self, thread_id: str) -> None:
        self.client.beta.threads.delete(thread_id=thread_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_files(self):  # type: ignore
        return self.client.files.list()

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_file(self, file_id: str) -> None:
        self.client.files.delete(file_id)

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def list_assistants(self):  # type: ignore
        return self.client.beta.assistants.list(limit=100).data

    @retry(wait=wait_random_exponential(min=1, max=400), stop=stop_after_attempt(100))
    def delete_assistant(self, assistant_id: str) -> None:
        self.client.beta.assistants.delete(assistant_id)
