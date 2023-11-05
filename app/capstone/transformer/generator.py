import pdfplumber
from pptx import Presentation  # type: ignore
from .models import Conversion, File, User
from typing import List, Dict
from .presentationGenerator import PresentationGenerator
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
from django.core.exceptions import ObjectDoesNotExist
import os


def pdf_to_text(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def multiple_pdf_to_text(paths: List[str]) -> dict[str, str]:
    result = {}
    for path in paths:
        result[path] = pdf_to_text(path)
    return result


# We will need this later
# def pptx_to_pdf(pptx_filename, pdf_filename):
#     prs = Presentation(pptx_filename)

#     c = canvas.Canvas(pdf_filename, pagesize=letter)

#     for slide in prs.slides:
#         c.setPageSize((slide.slide_width, slide.slide_height))

#         for shape in slide.shapes:
#             if shape.has_text_frame:
#                 for paragraph in shape.text_frame.paragraphs:
#                     for run in paragraph.runs:
#                         text = run.text
#                         c.drawString(100, 100, text)

#         c.showPage()

#     c.save()


def generate_output(files: List[File], conversion: Conversion) -> None:
    texts = multiple_pdf_to_text([f.file.path for f in files])

    pres_manager = PresentationGenerator(
        "gpt-3.5-turbo", texts, conversion, temperature=1
    )

    output_file_path = pres_manager.build_presentation()
    file_name, file_extension = os.path.splitext(output_file_path)

    user = None

    if conversion.user_id is not None:
        try:
            user = User.objects.get(id=conversion.user_id)
        except ObjectDoesNotExist:
            user = None

    new_file = File(
        user=user,
        conversion=conversion,
        type=file_extension,
        file=output_file_path,
        is_output=True,
    )
    new_file.save()
