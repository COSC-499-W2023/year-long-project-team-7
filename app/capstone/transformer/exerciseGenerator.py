from .models import Exercise


class ExerciseGenerator:
    def __init__(self, input_file_text: str, exercise: Exercise):
        #need to create exercise manager
        #self.exercise_manager = ExerciseManager()

        #need to add openAI manager with exercise inputs

        self.exercise = exercise

        self.num_true_false = exercise.num_true_false
        self.num_multiple_choice = exercise.num_multiple_choice
        self.num_short_ans = exercise.num_short_ans
        self.num_long_ans = exercise.num_long_ans
        self.template = exercise.template
