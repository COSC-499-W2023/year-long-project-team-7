import pdfplumber
from markdownify import markdownify as md


def pdf_to_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def multiple_pdf_to_text(paths):
    result = {}
    for path in paths:
        result[path] = pdf_to_text(path)
    return result

# This will be where the magic happens
def generate_output(files, conversion):
    texts = multiple_pdf_to_text([f.file.path for f in files])
    return None