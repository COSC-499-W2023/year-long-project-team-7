from enum import Enum
from .openAiManager import OpenAiManager
from .presentationManager import (
    FieldTypes,
    PresentationManager,
    SlideContent,
    SlideTypes,
)
from .models import Conversion, Exercise
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
    def __init__(self, conv_or_ex: Conversion | Exercise):
        if conv_or_ex.template is not None:
            self.presentation_manager = PresentationManager(conv_or_ex.template)
            self.template = conv_or_ex.template
        else:
            raise Exception("Template not found")

        self.openai_manager = OpenAiManager(conv_or_ex.model)

        if isinstance(conv_or_ex, Conversion):
            self.conversion = conv_or_ex
            self.num_slides = conv_or_ex.num_slides
            self.image_frequency = conv_or_ex.image_frequency
        elif isinstance(conv_or_ex, Exercise):
            self.exercise = conv_or_ex
            self.num_multiple_choice = conv_or_ex.num_multiple_choice
            self.num_true_false = conv_or_ex.num_true_false
            self.num_short_ans = conv_or_ex.num_short_ans

    def add_slides(
        self, slide_contents: list[SlideContent], conv_or_ex: Conversion | Exercise
    ) -> None:
        sorted_slide_contents = sorted(
            slide_contents, key=lambda slide: slide.slide_num
        )

        json_contents = []
        for slide_content in sorted_slide_contents:
            json_contents.append(slide_content.to_json())
            self.presentation_manager.add_slide_to_presentation(slide_content)

        conv_or_ex.slides_contents = json.dumps(json_contents)

        conv_or_ex.save()

    def image_search(self, query: str) -> str:
        query = re.sub("<|>", "", query)

        params = {
            "engine": "google_images",
            "q": query,
            "location": "Austin, TX, Texas, United States",
            "api_key": settings.SERP_API_KEY,  # type: ignore
        }

        search = GoogleSearch(params)

        results = search.get_dict()["images_results"]

        while True:
            try:
                random_image_url = results[random.randint(0, len(results) - 1)][
                    "original"
                ]
            except KeyError as e:
                print(random_image_url)
                error(e)
                continue

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
        return file_system.path(image_file.file.name)

    def generate_slide_content(
        self,
        slide_num: int,
        slide_type: SlideTypes,
        regenerate: bool = False,
        prompt: str = "",
    ) -> SlideContent:
        if slide_type == SlideTypes.TITLE:
            layout = self.presentation_manager.get_title_slide_layout()
        elif slide_type == SlideTypes.IMAGE:
            layout = self.presentation_manager.get_image_slide_layout()
        elif slide_type in [
            SlideTypes.CONTENT,
            SlideTypes.MULTIPLE_CHOICE,
            SlideTypes.TRUE_FALSE,
            SlideTypes.SHORT_ANSWER,
        ]:
            layout = self.presentation_manager.get_content_slide_layout()

        fields = self.presentation_manager.get_slide_layout_fields(layout, slide_type)

        slide_content = SlideContent(slide_num, layout.name, fields)

        slide_json = slide_content.to_json_string()

        if regenerate:
            response = self.openai_manager.prompt_chat(
                Prompts.UPDATE_SLIDE.format(slide_json=slide_json, prompt=prompt)
            )
        elif slide_type in [SlideTypes.TITLE, SlideTypes.CONTENT, SlideTypes.IMAGE]:
            response = self.openai_manager.prompt_chat(
                Prompts.SLIDE.format(slide_json=slide_json)
            )
        elif slide_type == SlideTypes.MULTIPLE_CHOICE:
            response = self.openai_manager.prompt_chat(
                Prompts.MULTIPLE_CHOICE_EXERCISE.format(slide_json=slide_json)
            )
        elif slide_type == SlideTypes.TRUE_FALSE:
            response = self.openai_manager.prompt_chat(
                Prompts.TRUE_FALSE_EXERCISE.format(slide_json=slide_json)
            )
        elif slide_type == SlideTypes.SHORT_ANSWER:
            response = self.openai_manager.prompt_chat(
                Prompts.SHORT_ANSWER_EXERCISE.format(slide_json=slide_json)
            )

        try:
            slide_content.update_from_json(response)
        except Exception as e:
            error(e)

        if slide_type == SlideTypes.IMAGE:
            for field in slide_content.fields:
                if field.field_type == FieldTypes.IMAGE:
                    if isinstance(field.value, str):
                        field.value = self.image_search(field.value)

        return slide_content

    # Executed in parallel
    def new_slide(self, slide_num: int) -> SlideContent:
        image_slide_likelihood = {0: 0, 1: 0.2, 2: 0.3, 3: 0.4, 4: 0.6, 5: 0.7, 6: 0.8}

        is_image_slide = random.random() < image_slide_likelihood[self.image_frequency]

        slide_type = (
            SlideTypes.IMAGE
            if is_image_slide
            else SlideTypes.TITLE
            if slide_num == 1
            else SlideTypes.CONTENT
        )

        return self.generate_slide_content(slide_num, slide_type)

    def update_slide(self, update_slide_params: SlideToBeUpdated) -> SlideContent:
        slide_num = update_slide_params.slide_number
        is_image_slide = update_slide_params.is_image_slide
        prompt = update_slide_params.prompt

        slide_type = (
            SlideTypes.IMAGE
            if is_image_slide
            else SlideTypes.TITLE
            if slide_num == 1
            else SlideTypes.CONTENT
        )

        return self.generate_slide_content(
            slide_num, slide_type, regenerate=True, prompt=prompt
        )

    def new_question_slide(
        self, slide_num: int, slide_type: SlideTypes
    ) -> SlideContent:
        return self.generate_slide_content(slide_num, slide_type)

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

        self.add_slides(slide_contents, self.conversion)

        return self.presentation_manager.save_presentation(self.conversion.id)

    def build_excercise(
        self, input_file_text: str, slide_types: list[SlideTypes]
    ) -> str:
        self.presentation_manager.delete_all_slides()

        system_prompt = Prompts.EXERCISES.format(
            language=self.exercise.language,
            complexity=self.exercise.complexity,
            prompt=self.exercise.prompt,
            input_file_text=input_file_text,
        )

        self.openai_manager.set_system_prompt(system_prompt)

        slide_contents: list[SlideContent] = []

        # Fetch slide content in parallel for speed
        with ThreadPoolExecutor() as executor:
            future_slides = executor.map(
                lambda args: self.new_question_slide(*args), enumerate(slide_types, 1)
            )
            slide_contents = list(future_slides)

        self.add_slides(slide_contents, self.exercise)

        return self.presentation_manager.save_presentation(self.exercise.id)

    def regenerate_slides(
        self,
        slides_to_be_updated: list[SlideToBeUpdated],
        input_file_text: str,
        new_conversion: Conversion,
    ) -> str:
        self.presentation_manager.delete_all_slides()

        system_prompt = Prompts.PRESENTATION.format(
            tone=self.conversion.tone,
            language=self.conversion.language,
            complexity=self.conversion.complexity,
            prompt=self.conversion.prompt,
            input_file_text=input_file_text,
        )

        self.openai_manager.set_system_prompt(system_prompt)

        existing_slides_contents = json.loads(self.conversion.slides_contents)
        existing_slides_contents = [
            SlideContent(json=content) for content in existing_slides_contents
        ]

        updated_slide_contents: list[SlideContent] = []

        # Fetch slide content in parallel for speed
        with ThreadPoolExecutor() as executor:
            future_slides = executor.map(
                lambda slide: self.update_slide(slide), slides_to_be_updated
            )
            updated_slide_contents = list(future_slides)

        combined_slides: dict[int, SlideContent] = {}

        for existing_slide in existing_slides_contents:
            combined_slides[existing_slide.slide_num] = existing_slide

        for updated_slide in updated_slide_contents:
            if updated_slide.slide_num in combined_slides:
                combined_slides[updated_slide.slide_num] = updated_slide

        # Now convert the dictionary values to a list
        combined_slides_list = list(combined_slides.values())
        self.add_slides(combined_slides_list, new_conversion)

        return self.presentation_manager.save_presentation(new_conversion.id)
