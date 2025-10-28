import gradio as gr
from transformers import MarianMTModel, MarianTokenizer
from concurrent.futures import ThreadPoolExecutor
from document_processor import process_document, segment_text
from document_output import create_txt_file, create_docx_file, create_pdf_file
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

def translate_document(file, output_format, progress=gr.Progress()):
    """Translate uploaded document with complete segment tracking"""
    if file is None:
        return "Please upload a document first.", None
    
    try:
        progress(0, desc="Extracting text...")
        text = process_document(file)
        
        progress(0.2, desc="Segmenting text...")
        segments = segment_text(text)
        total_segments = len(segments)
        
        if total_segments == 0:
            return "No text found in document.", None
        
        progress(0.3, desc=f"Translating {total_segments} segments...")
        
        # Track translation results
        translated_segments = []
        failed_segments = []
        
        # Parallel translation with result tracking
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all translation tasks
            future_to_index = {executor.submit(translate_segment, segment): i 
                             for i, segment in enumerate(segments)}
            
            # Collect results with tracking
            results = [None] * total_segments
            completed = 0
            
            for future in future_to_index:
                index = future_to_index[future]
                try:
                    result = future.result()
                    # Check if translation failed
                    if result.startswith("Error:"):
                        failed_segments.append(index + 1)
                        results[index] = f"[TRANSLATION FAILED: Segment {index + 1}]"
                    else:
                        results[index] = result
                    
                    completed += 1
                    progress(0.3 + (completed / total_segments) * 0.6, 
                           desc=f"Translated {completed}/{total_segments} segments")
                    
                except Exception as e:
                    failed_segments.append(index + 1)
                    results[index] = f"[TRANSLATION FAILED: Segment {index + 1}]"
                    completed += 1
        
        # Verify all segments were processed
        if None in results:
            missing_count = results.count(None)
            return f"Translation incomplete: {missing_count} segments failed to process.", None
        
        # Check for failed translations
        if failed_segments:
            error_msg = f"Translation completed with errors in segments: {', '.join(map(str, failed_segments))}\n\n"
            error_msg += "\n\n".join(results)
            return error_msg, None
        
        # All segments successfully translated
        translated_text = "\n\n".join(results)
        
        progress(0.9, desc="Creating download file...")
        
        # Create downloadable file based on format
        if output_format == "TXT":
            file_path = create_txt_file(translated_text)
        elif output_format == "DOCX":
            file_path = create_docx_file(translated_text)
        elif output_format == "PDF":
            file_path = create_pdf_file(translated_text)
        else:
            file_path = create_txt_file(translated_text)
        
        progress(1.0, desc=f"Complete! All {total_segments} segments translated successfully.")
        success_msg = f"✅ Translation completed successfully!\n{total_segments} segments processed.\n\n{translated_text}"
        return success_msg, file_path
        
    except Exception as e:
        return f"Document processing error: {str(e)}", None

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
                    output_format = gr.Dropdown(
                        choices=["TXT", "DOCX", "PDF"],
                        value="TXT",
                        label="Output Format"
                    )
                    translate_btn = gr.Button("Translate Document", variant="primary")
                
                with gr.Column():
                    output_text = gr.Textbox(
                        label="Arabic Translation",
                        lines=15,
                        max_lines=25
                    )
                    download_file = gr.File(
                        label="Download Translated Document",
                        visible=True
                    )
            
            translate_btn.click(
                fn=translate_document,
                inputs=[file_input, output_format],
                outputs=[output_text, download_file]
            )

if __name__ == "__main__":
    demo.launch()