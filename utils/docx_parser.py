from docx import Document


def extract_text_from_docx(file_path):

    text = ""

    document = Document(file_path)

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"

    return text