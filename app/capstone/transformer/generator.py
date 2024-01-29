import pdfplumber
from pptx import Presentation  # type: ignore
from .models import Conversion, File, User
from .presentationGenerator import PresentationGenerator
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from striprtf.striprtf import rtf_to_text  # type: ignore
from docx import Document  # type: ignore
from striprtf.striprtf import rtf_to_text
import os
import subprocess
from django.conf import settings

def pptx_to_pdf(pptx_filename: str) -> str:
    file_system = FileSystemStorage()
    file_path = file_system.path(pptx_filename)
    files_location = file_system.base_location
    base_name, extension = pptx_filename.rsplit(".", 1)

    command = f"soffice --headless --convert-to pdf --outdir {files_location} {file_path}" if settings.IS_DEV else f"HOME=/var/lib/www-libreoffice soffice --headless --convert-to pdf --outdir {files_location} {file_path}"

    subprocess.run(command, shell=True, check=True)

    return f"{base_name}.pdf"


def generate_output(files: list[File], conversion: Conversion) -> None:
    pres_manager = PresentationGenerator([f.file.path for f in files], conversion)

    output_file_path = pres_manager.build_presentation()
    # output_file_path = "nothing.pptx"
    file_name, file_extension = os.path.splitext(output_file_path)

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
        file=output_file_path,
        is_output=True,
    )
    new_pptx.save()

    pdf_preview_path = pptx_to_pdf(output_file_path)
    new_pdf = File(
        user=user,
        conversion=conversion,
        type="pdf",
        file=pdf_preview_path,
        is_output=True,
    )
    new_pdf.save()
