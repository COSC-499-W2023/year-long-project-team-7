from .models import Exercise
from .exerciseManager import (
    FieldTypes,
    ExerciseManager,
    ExerciseContent,
)
from .utils import error
from concurrent.futures import ThreadPoolExecutor
from .prompts import *
from .openAiManager import OpenAiExerciseManager

class ExerciseGenerator:
    def __init__(self, input_file_text: str, exercise: Exercise):
        self.exercise_manager = ExerciseManager()

        self.openai_manager = OpenAiExerciseManager(input_file_text, exercise)

        self.exercise = exercise

        self.num_true_false = exercise.num_true_false
        self.num_multiple_choice = exercise.num_multiple_choice
        self.num_short_ans = exercise.num_short_ans
        self.num_long_ans = exercise.num_long_ans
        self.num_slides = exercise.num_true_false + exercise.num_multiple_choice + exercise.num_short_ans + exercise.num_long_ans
        self.template = exercise.template

    def build_slide(self, slide_num: int) -> ExerciseContent:
        layout = self.exercise_manager.get_content_slide_layout()

        fields = self.exercise_manager.get_slide_layout_fields(layout)

        exercise_content = ExerciseContent(slide_num, layout, fields)

        exercise_json = exercise_content.to_json_string()

        response = self.openai_manager.prompt_chat(EXERCISE.format(slide_json=exercise_json))

        try:
            exercise_content.update_from_json(response)
        except Exception as e:
            error(e)

        return exercise_content

    def build_presentation(self) -> str:
        if self.template is not None:
            self.exercise_manager.setup(self.template)

        slide_contents: list[ExerciseContent] = []

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
            self.exercise_manager.add_slide_to_presentation(slide_content)

        return self.exercise_manager.save_presentation(self.exercise.id)