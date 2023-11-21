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
from docx import Document # type: ignore
from striprtf.striprtf import rtf_to_text # type: ignore
import os


def detect_file_type(paths: List[str]) -> List[str]:
    type_str = []
    path_str = []

    for path in paths:
        file_name, file_extension = os.path.splitext(path)
        type_str.append(file_extension)
        path_str.append(file_name)

    for i in range(len(type_str)):
        if(type_str[i] == '.pptx'):
            newpath = path_str[i] + '.pdf'
            pptx_to_pdf(paths[i], newpath)
            paths[i] = newpath
        elif(type_str[i] == '.docx' or type_str[i] == '.doc'):
            newpath = path_str[i] + '.pdf'
            docx_to_pdf(paths[i], newpath)
            paths[i] = newpath
        elif(type_str[i] == '.txt'):
            newpath = path_str[i] + '.pdf'
            txt_to_pdf(paths[i], newpath)
            paths[i] = newpath
        elif(type_str[i] == '.rtf'):
            newpath = path_str[i] + '.pdf'
            rtf_to_pdf(paths[i], newpath)
            paths[i] = newpath
        elif(type_str[i] == '.pdf'):
            paths[i] = paths[i]
    
    return paths

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


def pptx_to_pdf(pptx_filename: str, pdf_filename: str) -> None:
    prs = Presentation(pptx_filename)
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    for slide in prs.slides:
        i = 750
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        text = run.text
                        c.drawString(15, i, text)
                        i = i - 12
                        if(i < 100):
                            i = 750
                            c.showPage()
        c.showPage()
    c.save()

def docx_to_pdf(docx_filename: str, pdf_filename: str) -> None:
    #convert(docx_filename, pdf_filename)
    doc = Document(docx_filename)
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    i = 750
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            text = run.text
            c.drawString(15, i, text)
            i = i - 12
            if(i < 100):
                i = 750
                c.showPage()
    c.showPage()
    c.save()

def txt_to_pdf(txt_filename: str, pdf_filename: str) -> None:
    lines = open(txt_filename, 'r').read().splitlines()
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    i = 750
    for j in range(len(lines)):
        c.drawString(15, i, lines[j])
        i = i - 12
        if(j % 20 == 0 & j != 0):
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
        if(j % 20 == 0 & j != 0):
            c.showPage()
    c.showPage()
    c.save()

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
