from pptx import Presentation  # type: ignore


class PresentationManager:
    def set_presenetation(self, presentation: Presentation) -> None:
        self.presentation = presentation

    def get_slides(self) -> None:
        return None

    def get_title_slide_layout(self) -> None:
        return None

    def get_image_slide_layout(self) -> None:
        return None

    def get_content_slide_layout(self) -> None:
        return None
