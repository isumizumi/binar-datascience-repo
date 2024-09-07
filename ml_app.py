import re
import gradio as gr

def data_processing(text):
    return re.sub(r'[^a-zA-Z0-9]', ' ', text)

gradio_ui = gr.Interface(
    fn=data_processing,
    title="Data Processing and Modelling",
    description="This application processes input text to extract only letters and numbers using regex.",
    inputs=gr.Textbox(lines=10, label="Enter your text"),
    outputs=[gr.Textbox(label="Result"),
             ],
)

gradio_ui.launch()