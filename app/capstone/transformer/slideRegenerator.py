from .models import Conversion


class SlideToBeUpdated:
    def __init__(
        self,
        slide_number: int,
        prompt: str,
        is_image_slide: bool,
        conversion: Conversion,
    ):
        self.slide_number = slide_number
        self.prompt = prompt
        self.is_image_slide = is_image_slide
        self.conversion = conversion


class SlideRegenerator:
    def regenerate_slides(self, slides_to_be_updated: list[SlideToBeUpdated]) -> None:
        pass

    def regenerate_slide(self, slide_to_be_updated: SlideToBeUpdated) -> None:
        pass
