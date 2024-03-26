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


def reprompt_slides(
    slides_to_be_updated: list[SlideToBeUpdated], old_conversion: Conversion
) -> Conversion:
    new_conversion = Conversion.objects.create(
        prompt=old_conversion.prompt,
        language=old_conversion.language,
        tone=old_conversion.tone,
        complexity=old_conversion.complexity,
        num_slides=old_conversion.num_slides,
        image_frequency=old_conversion.image_frequency,
        user=old_conversion.user,
    )

    old_conversion_files = list(File.objects.filter(conversion=old_conversion))
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
        slides_to_be_updated, input_file_text, new_conversion
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
