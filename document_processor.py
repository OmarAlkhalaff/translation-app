import PyPDF2
from docx import Document
import nltk
from io import BytesIO

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    doc = Document(BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_bytes):
    """Extract text from TXT file"""
    return file_bytes.decode('utf-8')

def segment_text(text, max_chars=400):
    """Split text into segments for translation"""
    sentences = nltk.sent_tokenize(text)
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        if len(current_segment + sentence) <= max_chars:
            current_segment += sentence + " "
        else:
            if current_segment:
                segments.append(current_segment.strip())
            current_segment = sentence + " "
    
    if current_segment:
        segments.append(current_segment.strip())
    
    return segments

def process_document(file):
    """Process uploaded document and extract text"""
    file_extension = file.name.lower().split('.')[-1]
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file.read())
    elif file_extension == 'docx':
        text = extract_text_from_docx(file.read())
    elif file_extension == 'txt':
        text = extract_text_from_txt(file.read())
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return text