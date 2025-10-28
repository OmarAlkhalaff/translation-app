from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile

def create_txt_file(text, filename="translation.txt"):
    """Create a downloadable TXT file"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    temp_file.write(text)
    temp_file.close()
    return temp_file.name

def create_docx_file(text, filename="translation.docx"):
    """Create a downloadable DOCX file"""
    doc = Document()
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    for paragraph in paragraphs:
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
    doc.save(temp_file.name)
    temp_file.close()
    return temp_file.name

def create_pdf_file(text, filename="translation.pdf"):
    """Create a downloadable PDF file with Arabic text support"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    width, height = letter
    
    # Set up for Arabic text (right-to-left)
    y_position = height - 50
    margin = 50
    line_height = 20
    
    # Split text into lines that fit the page width
    lines = []
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if paragraph.strip():
            # Simple line wrapping (basic implementation)
            words = paragraph.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) * 6 < (width - 2 * margin):  # Rough character width estimation
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            lines.append("")  # Empty line between paragraphs
    
    # Write lines to PDF
    for line in lines:
        if y_position < margin:
            c.showPage()
            y_position = height - 50
        
        c.drawString(margin, y_position, line)
        y_position -= line_height
    
    c.save()
    temp_file.close()
    return temp_file.name