import pdfplumber
from .models import Conversion, File
from typing import List, Dict
import openai
from .openaiManager import OpenAiManager

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


def generate_output(files: List[File], conversion: Conversion) -> dict[str, str]:
    texts = multiple_pdf_to_text([f.file.path for f in files])

    manager = OpenAiManager(texts, conversion)

    return texts


