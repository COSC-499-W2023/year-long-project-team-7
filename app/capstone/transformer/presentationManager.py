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
        fields: dict[SlideFieldTypes, int],
        content: dict[SlideFieldTypes, typing.Union[str, File]],
    ):
        self.slide_type = slide_type
        self.slide_num = slide_num
        self.layout = layout
        self.fields = fields
        self.content = content


class PresentationManager:
    def __init__(self) -> None:
        pass

    def setup(self, template_path: str) -> None:
        self.template_path = template_path
        self.presentation = Presentation(template_path)

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

        return random.choice(potential_layouts)

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

        self.delete_all_slides()
        return random.choice(potential_layouts)

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

        return random.choice(potential_layouts)

    def get_slide_layout_fields(self, layout: typing.Any) -> dict[SlideFieldTypes, int]:
        fields = {}
        temp_presentation = Presentation(self.template_path)
        temp_slide = temp_presentation.slides.add_slide(layout)
        shapes = temp_slide.shapes
        for shape in shapes:  # Use enumerate to get both index and shape
            if shape.is_placeholder:
                phf = shape.placeholder_format
                if phf.type == PP_PLACEHOLDER.TITLE:
                    fields[SlideFieldTypes.TITLE] = shapes.index(
                        shape
                    )  # Use index for position
                elif phf.type == PP_PLACEHOLDER.BODY:
                    fields[SlideFieldTypes.TEXT] = shapes.index(
                        shape
                    )  # Use index for position
                elif phf.type == PP_PLACEHOLDER.PICTURE:
                    fields[SlideFieldTypes.IMAGE] = shapes.index(
                        shape
                    )  # Use index for position
                continue
            if shape.shape_type == MSO_SHAPE_TYPE.TEXT_BOX:
                fields[SlideFieldTypes.TEXT] = shapes.index(
                    shape
                )  # Use index for TEXT box shapes
            elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                fields[SlideFieldTypes.IMAGE] = shapes.index(
                    shape
                )  # Use index for PICTURE shapes

        return fields

    def add_slide_to_presentation(self, slide_content: SlideContent) -> None:
        slide = self.presentation.slides.add_slide(slide_content.layout)
        fields = slide_content.fields
        content = slide_content.content

        for key, value in content.items():
            if key == SlideFieldTypes.TITLE:
                slide.shapes[fields[key]].text = value
            elif key == SlideFieldTypes.TEXT:
                slide.shapes[fields[key]].text = value
            elif key == SlideFieldTypes.IMAGE:
                slide.shapes[fields[key]].insert_picture(value)
