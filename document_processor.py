import PyPDF2
from docx import Document
import nltk
from io import BytesIO

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

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
    try:
        sentences = nltk.sent_tokenize(text)
    except LookupError:
        # Fallback to simple splitting if NLTK fails
        sentences = text.split('. ')
        sentences = [s + '.' for s in sentences[:-1]] + [sentences[-1]]
    
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
    # Handle Gradio file object
    if hasattr(file, 'name'):
        file_path = file.name
    else:
        file_path = file
    
    file_extension = file_path.lower().split('.')[-1]
    
    # Read file content
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_bytes)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file_bytes)
    elif file_extension == 'txt':
        text = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return text