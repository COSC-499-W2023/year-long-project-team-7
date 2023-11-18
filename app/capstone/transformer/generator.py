import pdfplumber
from pptx import Presentation  # type: ignore
from .models import Conversion, File, User
from .presentationGenerator import PresentationGenerator
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
from django.core.exceptions import ObjectDoesNotExist
import os


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


def generate_output(files: list[File], conversion: Conversion) -> None:
    pres_manager = PresentationGenerator([f.file.path for f in files], conversion)

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
