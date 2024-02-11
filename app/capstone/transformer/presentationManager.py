from enum import Enum
from io import BytesIO
import typing
from pptx import Presentation  # type: ignore
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
import random
from pptx.enum.shapes import PP_PLACEHOLDER  # type: ignore
from pptx.enum.shapes import MSO_SHAPE_TYPE
from .models import File


class SlideFieldTypes(Enum):
    TITLE = "TITLE"
    TEXT = "TEXT"
    IMAGE = "IMAGE"


class SlideTypes(Enum):
    TITLE = "TITLE"
    CONTENT = "CONTENT"
    IMAGE = "IMAGE"


class SlideContent:
    def __init__(
        self,
        slide_num: int,
        slide_type: SlideTypes,
        layout: typing.Any,
        fields: list[dict[SlideFieldTypes, int]],
        content: list[dict[SlideFieldTypes, typing.Union[str, File]]],
    ):
        self.slide_type = slide_type
        self.slide_num = slide_num
        self.layout = layout
        self.fields = fields
        self.content = content


class MissingPlaceHolderErros(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PresentationManager:
    def setup(self, template_path: str) -> None:
        file_system = FileSystemStorage()

        self.template_path = file_system.path(template_path)
        self.presentation = Presentation(self.template_path)

        self.delete_all_slides()

    def delete_all_slides(self) -> None:
        # Delete all slides from template presentation
        xml_slides = self.presentation.slides._sldIdLst
        slides = list(xml_slides)
        for slide in slides:
            rId = slide.get("r:id")
            if rId is not None:
                self.presentation.part.drop_rel(rId)
        xml_slides.clear()

    def save_presentation(self, conversion_id: int) -> str:
        file_system = FileSystemStorage()
        buffer = BytesIO()
        self.presentation.save(buffer)
        buffer.seek(0)
        file_content = ContentFile(buffer.read())

        rel_path = f"testing_id{conversion_id}.pptx"

        file_system.save(rel_path, file_content)

        return rel_path

    def get_title_slide_layout(self) -> typing.Any:
        potential_layouts = []

        temp_presentation = Presentation(self.template_path)

        for slide_layout in temp_presentation.slide_layouts:
            if "title" in slide_layout.name.lower():
                potential_layouts.append(slide_layout)
        try:
            return random.choice(potential_layouts)
        except IndexError:
            raise MissingPlaceHolderErros("Template does not have a title slide")

    def get_image_slide_layout(self) -> typing.Any:
        potential_layouts = []

        temp_presentation = Presentation(self.template_path)

        for slide_layout in temp_presentation.slide_layouts:
            temp_slide = temp_presentation.slides.add_slide(slide_layout)

            for shape in temp_slide.shapes:
                if shape.is_placeholder:
                    phf = shape.placeholder_format
                    if phf.type == PP_PLACEHOLDER.PICTURE:
                        potential_layouts.append(slide_layout)
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    potential_layouts.append(slide_layout)
        try:
            return random.choice(potential_layouts)
        except IndexError:
            raise MissingPlaceHolderErros(
                "Template does not have any image placeholders"
            )

    def get_content_slide_layout(self) -> typing.Any:
        potential_layouts = []

        temp_presentation = Presentation(self.template_path)

        for slide_layout in temp_presentation.slide_layouts:
            temp_slide = temp_presentation.slides.add_slide(slide_layout)

            for shape in temp_slide.shapes:
                if shape.is_placeholder:
                    phf = shape.placeholder_format
                    if phf.type == PP_PLACEHOLDER.BODY:
                        potential_layouts.append(slide_layout)
                    continue

                if shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX:
                    potential_layouts.append(slide_layout)
        try:
            return random.choice(potential_layouts)
        except IndexError:
            raise MissingPlaceHolderErros(
                "Template does not have any text placeholders"
            )

    def get_slide_layout_fields(
        self, layout: typing.Any
    ) -> list[dict[SlideFieldTypes, int]]:
        fields = []
        temp_presentation = Presentation(self.template_path)
        temp_slide = temp_presentation.slides.add_slide(layout)
        shapes = temp_slide.shapes
        for shape in shapes:
            if shape.is_placeholder:
                phf = shape.placeholder_format
                if phf.type == PP_PLACEHOLDER.TITLE:
                    fields.append({SlideFieldTypes.TITLE: shapes.index(shape)})

                elif phf.type == PP_PLACEHOLDER.BODY:
                    fields.append({SlideFieldTypes.TEXT: shapes.index(shape)})

                elif phf.type == PP_PLACEHOLDER.PICTURE:
                    fields.append({SlideFieldTypes.IMAGE: shapes.index(shape)})
                continue

            if shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX:
                fields.append({SlideFieldTypes.TEXT: shapes.index(shape)})

            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                fields.append({SlideFieldTypes.IMAGE: shapes.index(shape)})

        return fields

    def add_slide_to_presentation(self, slide_content: SlideContent) -> None:
        slide = self.presentation.slides.add_slide(slide_content.layout)
        fields = slide_content.fields
        slide_contents = slide_content.content

        titles, texts, images = [], [], []

        for item in slide_contents:
            for field_type, value in item.items():
                if field_type == SlideFieldTypes.TITLE:
                    titles.append(value)
                elif field_type == SlideFieldTypes.TEXT:
                    texts.append(value)
                elif field_type == SlideFieldTypes.IMAGE:
                    images.append(value)

        for field in fields:
            first_key, first_value = next(iter(field.items()))
            if first_key == SlideFieldTypes.TITLE:
                try:
                    title_content = random.choice(titles)
                    titles.remove(title_content)

                    slide.shapes[first_value].text = title_content
                except IndexError:
                    continue

            elif first_key == SlideFieldTypes.TEXT:
                try:
                    text_content = random.choice(texts)
                    texts.remove(text_content)

                    slide.shapes[first_value].text = text_content
                except IndexError:
                    continue

            elif first_key == SlideFieldTypes.IMAGE:
                try:
                    image_content = random.choice(images)
                    images.remove(image_content)

                    slide.shapes[first_value].insert_picture(image_content.file)  # type: ignore
                except IndexError:
                    continue
