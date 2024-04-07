import json
from .models import Conversion, File, User, Exercise
from .presentationGenerator import PresentationGenerator, SlideTypes, SlideContent
from .models import Conversion, File, User
from .presentationGenerator import PresentationGenerator, SlideToBeUpdated
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
import os
import subprocess
from django.conf import settings
import fitz  # type: ignore
from .utils import error


def to_pdf(filename: str) -> str:
    file_system = FileSystemStorage()
    file_path = file_system.path(filename)
    files_location = file_system.base_location
    base_name, extension = filename.rsplit(".", 1)

    command = (
        f"soffice --headless --convert-to pdf --outdir {files_location} {file_path}"
        if settings.IS_DEV  # type: ignore
        else f"HOME=/var/lib/www-libreoffice soffice --headless --convert-to pdf --outdir {files_location} {file_path}"
    )

    subprocess.run(command, shell=True, check=True)

    return f"{base_name}.pdf"


def extract_text_from_pdf(filename: str) -> str:
    file_system = FileSystemStorage()
    file_path = file_system.path(filename)
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_from_md(filename: str) -> str:
    file_system = FileSystemStorage()
    file_path = file_system.path(filename)
    text = open(file_path, "r").read()
    return text


def extract_text_from_multiple_files(files: list[File]) -> str:
    text = ""

    for file in files:
        ext = os.path.splitext(file.file.name)[1].lower()
        if "pdf" in file.type:
            text += extract_text_from_pdf(file.file.name)
        elif ext == ".md":
            text += extract_text_from_md(file.file.name)
        else:
            try:
                text += extract_text_from_pdf(to_pdf(file.file.name))
            except Exception as e:
                error(e)
    return text


def generate_presentation(files: list[File], conversion: Conversion) -> str:
    input_file_text = extract_text_from_multiple_files(files)

    presentation_generator = PresentationGenerator(conversion)

    new_presentation_path = presentation_generator.build_presentation(input_file_text)

    file_name, file_extension = os.path.splitext(new_presentation_path)

    user = None

    if conversion.user_id is not None:
        try:
            user = User.objects.get(id=conversion.user_id)
        except ObjectDoesNotExist:
            user = None

    new_pptx = File(
        user=user,
        conversion=conversion,
        type=file_extension,
        file=new_presentation_path,
        is_output=True,
    )
    new_pptx.save()

    pdf_preview_path = to_pdf(new_presentation_path)
    new_pdf = File(
        user=user,
        conversion=conversion,
        type="application/pdf",
        file=pdf_preview_path,
        is_output=True,
    )
    new_pdf.save()

    return new_presentation_path


def generate_exercise(files: list[File], exercise: Exercise) -> str:
    input_file_text = extract_text_from_multiple_files(files)

    presentation_generator = PresentationGenerator(exercise)

    slide_types = (
        [SlideTypes.MULTIPLE_CHOICE] * exercise.num_multiple_choice
        + [SlideTypes.TRUE_FALSE] * exercise.num_true_false
        + [SlideTypes.SHORT_ANSWER] * exercise.num_short_ans
    )

    output_file_name = presentation_generator.build_excercise(
        input_file_text, slide_types
    )

    file_name, file_extension = os.path.splitext(output_file_name)

    user = None

    if exercise.user_id is not None:
        try:
            user = User.objects.get(id=exercise.user_id)
        except ObjectDoesNotExist:
            user = None

    new_pptx = File(
        user=user,
        exercise=exercise,
        type=file_extension,
        file=output_file_name,
        is_output=True,
    )
    new_pptx.save()

    pdf_preview_path = to_pdf(output_file_name)
    new_pdf = File(
        user=user,
        exercise=exercise,
        type="application/pdf",
        file=pdf_preview_path,
        is_output=True,
    )
    new_pdf.save()

    return output_file_name


def reprompt_slides(
    slides_to_be_updated: list[SlideToBeUpdated], old_conv_or_ex: Conversion | Exercise
) -> Conversion | Exercise:
    if isinstance(old_conv_or_ex, Conversion):
        old_conversion = old_conv_or_ex
        new_conversion = Conversion.objects.create(
            prompt=old_conversion.prompt,
            language=old_conversion.language,
            template=old_conversion.template,
            tone=old_conversion.tone,
            complexity=old_conversion.complexity,
            num_slides=old_conversion.num_slides,
            image_frequency=old_conversion.image_frequency,
            user=old_conversion.user,
        )

        old_conversion_files = list(
            File.objects.filter(conversion=old_conversion, is_output=False)
        )
        for file in old_conversion_files:
            File.objects.create(
                user=file.user,
                conversion=new_conversion,
                type=file.type,
                file=file.file,
                is_input=file.is_input,
                is_output=file.is_output,
            )

        old_conversion_inputs = list(
            File.objects.filter(conversion=old_conversion, is_input=True)
        )
        input_file_text = extract_text_from_multiple_files(old_conversion_inputs)

        presentation_generator = PresentationGenerator(old_conversion)

        new_presentation_path = presentation_generator.regenerate_slides(
            slides_to_be_updated,
            input_file_text,
            new_conversion,
        )

        file_name, file_extension = os.path.splitext(new_presentation_path)

        user = None

        if old_conversion.user_id is not None:
            try:
                user = User.objects.get(id=old_conversion.user_id)
            except ObjectDoesNotExist:
                user = None

        new_pptx = File(
            user=user,
            conversion=new_conversion,
            type=file_extension,
            file=new_presentation_path,
            is_output=True,
        )
        new_pptx.save()

        pdf_preview_path = to_pdf(new_presentation_path)
        new_pdf = File(
            user=user,
            conversion=new_conversion,
            type="application/pdf",
            file=pdf_preview_path,
            is_output=True,
        )
        new_pdf.save()

        return new_conversion

    elif isinstance(old_conv_or_ex, Exercise):
        old_exercise = old_conv_or_ex
        old_exercise_slides_contents = [
            SlideContent(json=content)
            for content in json.loads(old_exercise.slides_contents)
        ]

        num_multiple_choice = old_exercise.num_multiple_choice
        num_true_false = old_exercise.num_true_false
        num_short_ans = old_exercise.num_short_ans

        for content in old_exercise_slides_contents:
            for slide in slides_to_be_updated:
                if content.slide_num == slide.slide_number:
                    if content.slide_type == SlideTypes.MULTIPLE_CHOICE:
                        num_multiple_choice -= 1
                    elif content.slide_type == SlideTypes.TRUE_FALSE:
                        num_true_false -= 1
                    elif content.slide_type == SlideTypes.SHORT_ANSWER:
                        num_short_ans -= 1

                    if slide.slide_type == SlideTypes.MULTIPLE_CHOICE:
                        num_multiple_choice += 1
                    elif slide.slide_type == SlideTypes.TRUE_FALSE:
                        num_true_false += 1
                    elif slide.slide_type == SlideTypes.SHORT_ANSWER:
                        num_short_ans += 1

        new_exercise = Exercise.objects.create(
            prompt=old_exercise.prompt,
            language=old_exercise.language,
            template=old_exercise.template,
            complexity=old_exercise.complexity,
            user=old_exercise.user,
            num_true_false=num_true_false,
            num_short_ans=num_short_ans,
            num_multiple_choice=num_multiple_choice,
        )

        old_exercise_files = list(
            File.objects.filter(exercise=old_exercise, is_output=False)
        )
        for file in old_exercise_files:
            File.objects.create(
                user=file.user,
                exercise=new_exercise,
                type=file.type,
                file=file.file,
                is_input=file.is_input,
                is_output=file.is_output,
            )

        old_exercise_inputs = list(
            File.objects.filter(exercise=old_exercise, is_input=True)
        )
        input_file_text = extract_text_from_multiple_files(old_exercise_inputs)

        presentation_generator = PresentationGenerator(old_exercise)

        new_exercise_path = presentation_generator.regenerate_slides(
            slides_to_be_updated,
            input_file_text,
            new_exercise,
        )

        file_name, file_extension = os.path.splitext(new_exercise_path)

        user = None

        if old_exercise.user_id is not None:
            try:
                user = User.objects.get(id=old_exercise.user_id)
            except ObjectDoesNotExist:
                user = None

        new_pptx = File(
            user=user,
            exercise=new_exercise,
            type=file_extension,
            file=new_exercise_path,
            is_output=True,
        )
        new_pptx.save()

        pdf_preview_path = to_pdf(new_exercise_path)
        new_pdf = File(
            user=user,
            exercise=new_exercise,
            type="application/pdf",
            file=pdf_preview_path,
            is_output=True,
        )
        new_pdf.save()

        return new_exercise
