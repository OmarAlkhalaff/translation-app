import gradio as gr
from transformers import MarianMTModel, MarianTokenizer
from concurrent.futures import ThreadPoolExecutor
from document_processor import process_document, segment_text
import time

# Load translation model
model_name = "Helsinki-NLP/opus-mt-en-ar"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

def translate_segment(text):
    """Translate a single text segment"""
    try:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        result = tokenizer.decode(translated[0], skip_special_tokens=True)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def translate_text(message, history):
    """Translate English text to Arabic"""
    try:
        return translate_segment(message)
    except Exception as e:
        return f"Translation error: {str(e)}"

def translate_document(file, progress=gr.Progress()):
    """Translate uploaded document"""
    if file is None:
        return "Please upload a document first."
    
    try:
        progress(0, desc="Extracting text...")
        text = process_document(file)
        
        progress(0.2, desc="Segmenting text...")
        segments = segment_text(text)
        
        progress(0.3, desc=f"Translating {len(segments)} segments...")
        
        # Parallel translation
        with ThreadPoolExecutor(max_workers=4) as executor:
            translated_segments = list(executor.map(translate_segment, segments))
        
        progress(1.0, desc="Complete!")
        return "\n\n".join(translated_segments)
        
    except Exception as e:
        return f"Document processing error: {str(e)}"

# Create interface with tabs
with gr.Blocks(title="🌍 English to Arabic Translator") as demo:
    gr.Markdown("# 🌍 English to Arabic Translator")
    gr.Markdown("Translate text or documents from English to Arabic using AI")
    
    with gr.Tabs():
        with gr.Tab("💬 Text Chat"):
            chat_interface = gr.ChatInterface(
                fn=translate_text,
                examples=[
                    "Hello, how are you?",
                    "I love learning new languages.",
                    "Technology is changing the world.",
                    "Welcome to our website."
                ]
            )
        
        with gr.Tab("📄 Document Translation"):
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="Upload Document",
                        file_types=[".pdf", ".docx", ".txt"]
                    )
                    translate_btn = gr.Button("Translate Document", variant="primary")
                
                with gr.Column():
                    output_text = gr.Textbox(
                        label="Arabic Translation",
                        lines=20,
                        max_lines=30
                    )
            
            translate_btn.click(
                fn=translate_document,
                inputs=[file_input],
                outputs=[output_text]
            )

if __name__ == "__main__":
    demo.launch()