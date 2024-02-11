from collections import Counter
import typing

from .openAiManager import OpenAiManager
from .presentationManager import (
    PresentationManager,
    SlideFieldTypes,
    SlideContent,
    SlideTypes,
    MissingPlaceHolderErros,
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


class PresentationGenerator:
    def __init__(self, input_file_paths: list[str], conversion: Conversion):
        self.presentation_manager = PresentationManager()
        self.openai_manager = OpenAiManager()
        self.conversion = conversion

        user_parameters = json.loads(conversion.user_parameters)

        self.num_slides = user_parameters.get("num_slides", 10)
        self.image_frequency = user_parameters.get("image_frequency", 3)

        self.openai_manager.setup_assistant(input_file_paths, user_parameters)
        self.template = user_parameters.get("template", 1)

    def image_search(self, query: str) -> File:
        api_url = "https://api.unsplash.com/search/photos"
        params = {"query": query, "client_id": settings.UNSPLASH_ACCESS_KEY}  # type: ignore

        response = requests.get(api_url, params=params).json()

        images = response["results"]
        image_url = images[random.randint(0, len(images) - 1)]["urls"]["raw"]

        image = requests.get(image_url).content

        file_system = FileSystemStorage()
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

        content: list[dict[SlideFieldTypes, typing.Union[str, File]]] = []

        is_image_slide = random.random() < image_slide_likelihood[self.image_frequency]

        if slide_num == 1:
            layout = self.presentation_manager.get_title_slide_layout()
            fields = self.presentation_manager.get_slide_layout_fields(layout)
            title = self.openai_manager.prompt_assistant(TITLE_SLIDE_TITLE)

            for field in fields:
                first_key, first_value = next(iter(field.items()))
                if first_key == SlideFieldTypes.TITLE:
                    content.append({first_key: title})
                elif first_key == SlideFieldTypes.TEXT:
                    content.append(
                        {
                            first_key: self.openai_manager.prompt_assistant(
                                TITLE_SLIDE_SUB_TITLE.format(title=title)
                            )
                        }
                    )

            return SlideContent(slide_num, SlideTypes.TITLE, layout, fields, content)

        elif is_image_slide:
            layout = self.presentation_manager.get_image_slide_layout()
            fields = self.presentation_manager.get_slide_layout_fields(layout)

            num_text_fields = sum(
                1 for field in fields if SlideFieldTypes.TEXT in field.keys()
            )

            slide_text = self.openai_manager.prompt_assistant(
                SLIDE.format(
                    slide_num=slide_num,
                    num_slides=self.num_slides,
                    num_text_fields=num_text_fields,
                )
            )

            slide_texts = slide_text.split("\n")

            content.append({SlideFieldTypes.TITLE: slide_texts[0]})

            slide_texts.pop(0)

            for index, text in enumerate(slide_texts):
                if index < num_text_fields:
                    content.append({SlideFieldTypes.TEXT: text})
                else:
                    break

            image_search_query = self.openai_manager.prompt_assistant(
                IMAGE_SEARCH.format(content=slide_text)
            )
            image = self.image_search(image_search_query)

            image_fields = [
                field for field in fields if SlideFieldTypes.IMAGE in field.keys()
            ]

            for field in image_fields:
                first_key, first_value = next(iter(field.items()))
                content.append({first_key: image})

            return SlideContent(slide_num, SlideTypes.IMAGE, layout, fields, content)

        else:
            layout = self.presentation_manager.get_image_slide_layout()
            fields = self.presentation_manager.get_slide_layout_fields(layout)

            num_text_fields = sum(
                1 for field in fields if SlideFieldTypes.TEXT in field.keys()
            )

            slide_text = self.openai_manager.prompt_assistant(
                SLIDE.format(
                    slide_num=slide_num,
                    num_slides=self.num_slides,
                    num_text_fields=num_text_fields,
                )
            )

            slide_texts = slide_text.split("\n")

            content.append({SlideFieldTypes.TITLE: slide_texts[0]})

            slide_texts.pop(0)

            for index, text in enumerate(slide_texts):
                if index < num_text_fields:
                    content.append({SlideFieldTypes.TEXT: text})
                else:
                    break

            return SlideContent(slide_num, SlideTypes.CONTENT, layout, fields, content)

    def build_presentation(self) -> str:
        self.presentation_manager.setup(f"template_{self.template}.pptx")

        slide_contents: list[SlideContent] = []

        # Fetch slide content in parallel for speed
        try:
            with ThreadPoolExecutor() as executor:
                future_slides = executor.map(
                    self.build_slide, range(1, self.num_slides + 1)
                )
                slide_contents = list(future_slides)
        except MissingPlaceHolderErros as e:
            print(e.message)
            return e.message

        # Sort and add slides to presentation
        sorted_slide_contents = sorted(
            slide_contents, key=lambda slide: slide.slide_num
        )

        for slide_content in sorted_slide_contents:
            self.presentation_manager.add_slide_to_presentation(slide_content)

        return self.presentation_manager.save_presentation(self.conversion.id)
