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
from docx import Document  # type: ignore
from striprtf.striprtf import rtf_to_text  # type: ignore
from docx import Document  # type: ignore
from striprtf.striprtf import rtf_to_text  # type: ignore
import os
import subprocess

#! This implementation does not work
# def pptx_to_pdf(pptx_filename: str, pdf_filename: str) -> None:
#     prs = Presentation(pptx_filename)
#     c = canvas.Canvas(pdf_filename, pagesize=letter)
#     for slide in prs.slides:
#         i = 750
#         for shape in slide.shapes:
#             if shape.has_text_frame:
#                 for paragraph in shape.text_frame.paragraphs:
#                     for run in paragraph.runs:
#                         text = run.text
#                         c.drawString(15, i, text)
#                         i = i - 12
#                         if(i < 100):
#                             i = 750
#                             c.showPage()
#         c.showPage()
#     c.save()


def pptx_to_pdf(pptx_filename: str) -> str:
    file_system = FileSystemStorage()
    file_path = file_system.path(pptx_filename)
    files_location = file_system.base_location
    base_name, extension = pptx_filename.rsplit(".", 1)

    command = (
        f"soffice --headless --convert-to pdf --outdir {files_location} {file_path}"
    )
    subprocess.run(command, shell=True, check=True)

    return f"{base_name}.pdf"


def docx_to_pdf(docx_filename: str, pdf_filename: str) -> None:
    # convert(docx_filename, pdf_filename)
    # convert(docx_filename, pdf_filename)
    doc = Document(docx_filename)
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    i = 750
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            text = run.text
            c.drawString(15, i, text)
            i = i - 12
            if i < 100:
                if i < 100:
                    i = 750
                    c.showPage()
    c.showPage()
    c.save()


def txt_to_pdf(txt_filename: str, pdf_filename: str) -> None:
    lines = open(txt_filename, "r").read().splitlines()
    lines = open(txt_filename, "r").read().splitlines()
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    i = 750
    for j in range(len(lines)):
        c.drawString(15, i, lines[j])
        i = i - 12
        if j % 20 == 0 & j != 0:
            if j % 20 == 0 & j != 0:
                c.showPage()
    c.showPage()
    c.save()


def rtf_to_pdf(rtf_filename: str, pdf_filename: str) -> None:
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    with open(rtf_filename) as infile:
        line = infile.read()
    text = rtf_to_text(line)
    lines = text.splitlines()
    i = 750
    for j in range(len(lines)):
        c.drawString(15, i, lines[j])
        i = i - 12
        if j % 20 == 0 & j != 0:
            if j % 20 == 0 & j != 0:
                c.showPage()
    c.showPage()
    c.save()


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

    new_pptx = File(
        user=user,
        conversion=conversion,
        type=file_extension,
        file=output_file_path,
        is_output=True,
    )

    pdf_preview_path = pptx_to_pdf(output_file_path)

    new_pdf = File(
        user=user,
        conversion=conversion,
        type="pdf",
        file=pdf_preview_path,
        is_output=True,
    )

    new_pptx.save()
    new_pdf.save()
