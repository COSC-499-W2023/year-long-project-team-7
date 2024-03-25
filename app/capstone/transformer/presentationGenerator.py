from .openAiManager import OpenAiManager
from .presentationManager import (
    FieldTypes,
    PresentationManager,
    SlideContent,
)
from .models import Conversion
from django.conf import settings
import json
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
import random
import requests
from .models import File
from concurrent.futures import ThreadPoolExecutor
from .prompts import *
from serpapi import GoogleSearch  # type: ignore
from .utils import error
from urllib3.exceptions import MaxRetryError
import re


class SlideToBeUpdated:
    def __init__(
        self,
        slide_number: int,
        prompt: str,
        is_image_slide: bool,
    ):
        self.slide_number = slide_number
        self.prompt = prompt
        self.is_image_slide = is_image_slide


class PresentationGenerator:
    def __init__(self, conversion: Conversion):
        if conversion.template is not None:
            self.presentation_manager = PresentationManager(conversion.template)
        else:
            raise Exception("Template not found")
        self.openai_manager = OpenAiManager(conversion.model)

        self.conversion = conversion
        self.num_slides = conversion.num_slides
        self.image_frequency = conversion.image_frequency
        self.template = conversion.template

    def image_search(self, query: str) -> File:
        query = re.sub("<|>", "", query)

        params = {
            "engine": "google_images",
            "q": query,
            "location": "Austin, TX, Texas, United States",
            "api_key": settings.SERP_API_KEY,  # type: ignore
        }

        search = GoogleSearch(params)

        results = search.get_dict()["images_results"]

        jpegs_results = [
            result for result in results if str(result["original"]).endswith(".jpg")
        ]

        while True:
            random_image_url = results[random.randint(0, len(jpegs_results) - 1)][
                "original"
            ]

            try:
                response = requests.head(random_image_url)

                if "image/jpeg" in response.headers.get("content-type", ""):
                    image = requests.get(random_image_url).content
                    break

            except MaxRetryError as e:
                continue

        file_system = FileSystemStorage()

        name = f"{query[:30]}.jpg"
        path = file_system.save(name, ContentFile(image))

        image_file = File(
            user=self.conversion.user,
            conversion=self.conversion,
            type=".jpg",
            file=path,
            is_output=False,
        )

        image_file.save()
        return image_file

    def generate_slide_content(
        self,
        slide_num: int,
        is_image_slide: bool,
        regenerate: bool = False,
        prompt: str = "",
    ) -> SlideContent:
        if slide_num == 1:
            layout = self.presentation_manager.get_title_slide_layout()

        elif is_image_slide:
            layout = self.presentation_manager.get_image_slide_layout()

        else:
            layout = self.presentation_manager.get_content_slide_layout()

        fields = self.presentation_manager.get_slide_layout_fields(layout)

        slide_content = SlideContent(slide_num, layout, fields)

        slide_json = slide_content.to_json_string()

        if regenerate:
            response = self.openai_manager.prompt_chat(
                Prompts.UPDATE_SLIDE.format(slide_json=slide_json, prompt=prompt)
            )
        else:
            response = self.openai_manager.prompt_chat(
                Prompts.SLIDE.format(slide_json=slide_json)
            )

        try:
            slide_content.update_from_json(response)
        except Exception as e:
            error(e)

        if is_image_slide:
            for field in slide_content.fields:
                if field.field_type == FieldTypes.IMAGE:
                    if isinstance(field.value, str):
                        field.value = self.image_search(field.value)

        return slide_content

    # Executed in parallel
    def new_slide(self, slide_num: int) -> SlideContent:
        image_slide_likelihood = {0: 0, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.6, 5: 0.7, 6: 0.8}

        is_image_slide = random.random() < image_slide_likelihood[self.image_frequency]

        return self.generate_slide_content(slide_num, is_image_slide)

    def update_slide(self, update_slide_params: SlideToBeUpdated) -> SlideContent:
        slide_num = update_slide_params.slide_number
        is_image_slide = update_slide_params.is_image_slide
        prompt = update_slide_params.prompt

        return self.generate_slide_content(
            slide_num, is_image_slide, regenerate=True, prompt=prompt
        )

    def build_presentation(self, input_file_text: str) -> str:
        self.presentation_manager.delete_all_slides()

        system_prompt = Prompts.PRESENTATION.format(
            tone=self.conversion.tone,
            language=self.conversion.language,
            complexity=self.conversion.complexity,
            prompt=self.conversion.prompt,
            input_file_text=input_file_text,
        )

        self.openai_manager.set_system_prompt(system_prompt)

        slide_contents: list[SlideContent] = []

        # Fetch slide content in parallel for speed
        with ThreadPoolExecutor() as executor:
            future_slides = executor.map(self.new_slide, range(1, self.num_slides + 1))
            slide_contents = list(future_slides)

        # Sort and add slides to presentation
        sorted_slide_contents = sorted(
            slide_contents, key=lambda slide: slide.slide_num
        )

        for slide_content in sorted_slide_contents:
            self.presentation_manager.add_slide_to_presentation(slide_content)

        return self.presentation_manager.save_presentation(self.conversion.id)

    def regenerate_slides(
        self,
        slides_to_be_updated: list[SlideToBeUpdated],
        input_file_text: str,
        new_conversion: Conversion,
    ) -> str:
        system_prompt = Prompts.PRESENTATION.format(
            tone=self.conversion.tone,
            language=self.conversion.language,
            complexity=self.conversion.complexity,
            prompt=self.conversion.prompt,
            input_file_text=input_file_text,
        )

        self.openai_manager.set_system_prompt(system_prompt)

        slide_contents: list[SlideContent] = []

        # Fetch slide content in parallel for speed
        with ThreadPoolExecutor() as executor:
            future_slides = executor.map(
                lambda slide: self.update_slide(slide), slides_to_be_updated
            )
            slide_contents = list(future_slides)

        # Sort and add slides to presentation
        sorted_slide_contents = sorted(
            slide_contents, key=lambda slide: slide.slide_num
        )

        for slide_content in sorted_slide_contents:
            self.presentation_manager.update_slide(slide_content)

        return self.presentation_manager.save_presentation(self.conversion.id)
