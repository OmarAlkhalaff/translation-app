import gradio as gr
from transformers import MarianMTModel, MarianTokenizer
from concurrent.futures import ThreadPoolExecutor
from document_processor import process_document, segment_text
from document_output import create_txt_file, create_docx_file, create_pdf_file
import time
import tempfile

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
    """Translate uploaded document with table/figure support and complete tracking"""
    if file is None:
        return "Please upload a document first.", None
    
    try:
        progress(0, desc="Extracting text and elements...")
        text, element_processor = process_document(file)
        
        if text is None:
            return "Failed to extract text from document.", None
        
        # Handle documents with tables/figures (DOCX)
        if element_processor:
            progress(0.1, desc="Processing tables and figures...")
            
            # Translate tables if present
            table_errors = []
            for table_id in element_processor.tables:
                success = element_processor.translate_table_cells(table_id, translate_segment)
                if not success:
                    table_errors.append(table_id)
            
            # Check for element processing errors
            summary = element_processor.get_processing_summary()
            if summary['errors']:
                error_details = "\n".join([f"⚠️ {error}" for error in summary['errors']])
                if table_errors:
                    return f"Element processing failed:\n{error_details}", None
        
        progress(0.2, desc="Segmenting text...")
        segments, segment_placeholders = segment_text(text)
        total_segments = len(segments)
        
        if total_segments == 0:
            return "No text found in document.", None
        
        progress(0.3, desc=f"Translating {total_segments} segments...")
        
        # Track translation results
        failed_segments = []
        
        # Parallel translation with result tracking
        with ThreadPoolExecutor(max_workers=32) as executor:
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
                    progress(0.3 + (completed / total_segments) * 0.5, 
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
        
        # All segments successfully translated - now restore placeholders
        final_segments = []
        for seg_idx, translated_seg in enumerate(results):
            # Add translated text
            final_segments.append(translated_seg)
            # Add placeholders that belong after this segment
            if seg_idx in segment_placeholders:
                for placeholder in segment_placeholders[seg_idx]:
                    final_segments.append(placeholder)
        
        translated_text = "\n\n".join(final_segments)
        
        progress(0.85, desc="Creating download file...")
        
        # Create downloadable file based on format
        if output_format == "DOCX" and element_processor:
            # Enhanced DOCX with tables/figures
            temp_file = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
            success = element_processor.reconstruct_docx(translated_text, temp_file.name)
            if not success:
                # Fallback to simple DOCX
                file_path = create_docx_file(translated_text)
            else:
                file_path = temp_file.name
        elif output_format == "TXT":
            file_path = create_txt_file(translated_text)
        elif output_format == "DOCX":
            file_path = create_docx_file(translated_text)
        elif output_format == "PDF":
            file_path = create_pdf_file(translated_text)
        else:
            file_path = create_txt_file(translated_text)
        
        # Prepare success message with element summary
        success_msg = f"✅ Translation completed successfully!\n{total_segments} segments processed."
        
        if element_processor:
            summary = element_processor.get_processing_summary()
            if summary['tables']['total'] > 0 or summary['figures']['total'] > 0:
                success_msg += f"\n\n📄 Elements processed:"
                success_msg += f"\n• Tables: {summary['tables']['successful']}/{summary['tables']['total']}"
                success_msg += f"\n• Figures: {summary['figures']['successful']}/{summary['figures']['total']}"
                
                if summary['errors']:
                    success_msg += f"\n\n⚠️ Warnings:\n" + "\n".join([f"• {error}" for error in summary['errors']])
        
        progress(1.0, desc="Complete!")
        success_msg += f"\n\n{translated_text}"
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