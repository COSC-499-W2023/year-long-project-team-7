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


class PresentationGenerator:
    def __init__(self, input_file_text: str, conversion: Conversion, template: File):
        self.user_parameters = json.loads(conversion.user_parameters)

        self.presentation_manager = PresentationManager()

        self.openai_manager = OpenAiManager(input_file_text, self.user_parameters)
        self.conversion = conversion

        self.num_slides = self.user_parameters.get("num_slides", 10)
        self.image_frequency = self.user_parameters.get("image_frequency", 3)
        self.template = template

    def image_search(self, query: str) -> File:
        params = {
            "engine": "google_images",
            "q": query,
            "location": "Austin, TX, Texas, United States",
            "api_key": settings.SERP_API_KEY,  # type: ignore
        }

        search = GoogleSearch(params)

        results = search.get_dict()["images_results"]

        image_url = results[random.randint(0, len(results) - 1)]["original"]

        file_system = FileSystemStorage()

        image = requests.get(image_url).content

        rel_path = f"{query[:30]}.jpg"
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

    # Executed in parallel
    def build_slide(self, slide_num: int) -> SlideContent:
        image_slide_likelihood = {0: 0, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.6, 5: 0.7, 6: 0.8}

        is_image_slide = random.random() < image_slide_likelihood[self.image_frequency]

        if slide_num == 1:
            layout = self.presentation_manager.get_title_slide_layout()

        elif is_image_slide:
            layout = self.presentation_manager.get_image_slide_layout()

        else:
            layout = self.presentation_manager.get_content_slide_layout()

        fields = self.presentation_manager.get_slide_layout_fields(layout)

        slide_content = SlideContent(slide_num, layout, fields)

        slide_json = slide_content.to_json_string()

        response = self.openai_manager.prompt_chat(SLIDE.format(slide_json=slide_json))

        try:
            slide_content.update_from_json(response)
        except Exception as e:
            error(e)

        for field in slide_content.fields:
            if field.field_type == FieldTypes.IMAGE:
                if isinstance(field.value, str):
                    field.value = self.image_search(field.value)

        return slide_content

    def build_presentation(self) -> str:
        self.presentation_manager.setup(self.template)

        slide_contents: list[SlideContent] = []

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

        for slide_content in sorted_slide_contents:
            self.presentation_manager.add_slide_to_presentation(slide_content)

        return self.presentation_manager.save_presentation(self.conversion.id)
