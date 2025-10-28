import gradio as gr
from transformers import MarianMTModel, MarianTokenizer

# Load translation model
model_name = "Helsinki-NLP/opus-mt-en-ar"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

def translate_text(message, history):
    """Translate English text to Arabic"""
    try:
        # Tokenize and translate
        inputs = tokenizer(message, return_tensors="pt", padding=True)
        translated = model.generate(**inputs)
        result = tokenizer.decode(translated[0], skip_special_tokens=True)
        return result
    except Exception as e:
        return f"Translation error: {str(e)}"

# Create ChatGPT-like interface
demo = gr.ChatInterface(
    fn=translate_text,
    title="🌍 English to Arabic Translator",
    description="Enter English text and get Arabic translation instantly!",
    examples=[
        "Hello, how are you?",
        "I love learning new languages.",
        "Technology is changing the world.",
        "Welcome to our website."
    ]
)

if __name__ == "__main__":
    demo.launch()