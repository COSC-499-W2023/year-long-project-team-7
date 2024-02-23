from .models import Conversion, File, User
from .presentationGenerator import PresentationGenerator
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
import os
import subprocess
from django.conf import settings
import fitz  # type: ignore


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


def generate_output(files: list[File], template: File, conversion: Conversion) -> str:
    input_file_text = ""

    for file in files:
        if "pdf" in file.type:
            input_file_text += extract_text_from_pdf(file.file.name)
        else:
            try:
                input_file_text += extract_text_from_pdf(to_pdf(file.file.name))
            except Exception as e:
                print(e)

    pres_manager = PresentationGenerator(input_file_text, conversion, template)

    output_file_name = pres_manager.build_presentation()
    file_name, file_extension = os.path.splitext(output_file_name)

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
        file=output_file_name,
        is_output=True,
    )
    new_pptx.save()

    pdf_preview_path = to_pdf(output_file_name)
    new_pdf = File(
        user=user,
        conversion=conversion,
        type="application/pdf",
        file=pdf_preview_path,
        is_output=True,
    )
    new_pdf.save()

    return output_file_name
