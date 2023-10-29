import pdfplumber
from .models import Conversion, File, User
from typing import List, Dict
from .presentationGenerator import PresentationGenerator
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph  # type: ignore
from django.core.exceptions import ObjectDoesNotExist


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


def generate_output(files: List[File], conversion: Conversion) -> File:
    texts = multiple_pdf_to_text([f.file.path for f in files])

    pres_manager = PresentationGenerator(
        "gpt-3.5-turbo", texts, conversion, temprature=1
    )

    pres_manager.build_presentation()

    # pdf_file_path = f"files/conversion_ouput_{conversion.id}.pdf"

    # pdf = SimpleDocTemplate(pdf_file_path, pagesize=letter)
    # styles = getSampleStyleSheet()
    # flowables = [Paragraph(output_text, styles["Normal"])]
    # pdf.build(flowables)

    # user = None  # Initialize user to None by default

    # if conversion.user_id is not None:
    #     try:
    #         user = User.objects.get(id=conversion.user_id)
    #     except ObjectDoesNotExist:
    #         user = None

    # new_file = File(user=user, conversion=conversion, type="pdf", file=pdf_file_path)
    # new_file.save()

    return File()
