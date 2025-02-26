import os
import json
import requests
import gradio as gr
import PyPDF2

endpoints = {
    "chat-ai": {
        "url": "https://chat-ai.academiccloud.de/v1/chat/completions",
        "api_key": os.environ.get("CHAT_AI_API_TOKEN", "92bbad82caba7a2f0d0515bcf5a76cfc"),
        "model": "meta-llama-3.1-8b-instruct"
    },
    "ki@jlu": {
        "url": "https://ki-dev.hrz.uni-giessen.de/api/chat/completions",
        "api_key": os.environ.get("KI_JLU_API_TOKEN", "sk-3e59fba347a8499c8a19ffe1552cab91"),
        "model": "hrz-chat-small"
    }
}

def chat_with_file(endpoint_choice, system_prompt, user_input, uploaded_file):
    file_content = ""
    if uploaded_file is not None:
        # Check if file is a PDF based on its extension
        if uploaded_file.name.lower().endswith(".pdf"):
            try:
                with open(uploaded_file.name, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    extracted_text = ""
                    for page in reader.pages:
                        extracted_text += page.extract_text() or ""
                # Convert extracted text to a JSON string
                file_content = json.dumps({"pdf_text": extracted_text}, ensure_ascii=False)
            except Exception as e:
                return f"Error processing PDF file: {str(e)}"
        else:
            try:
                with open(uploaded_file.name, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                file_content = json.dumps({"file_text": content}, ensure_ascii=False)
            except Exception as e:
                return f"Error reading file: {str(e)}"

    if file_content:
        user_input += "\n\nFile Content:\n" + file_content

    selected = endpoints.get(endpoint_choice)
    if not selected:
        return "Invalid endpoint selection"

    headers = {
        "Authorization": f"Bearer {selected['api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": selected["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(selected["url"], json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks() as iface:
    gr.Markdown("### LLM Chat Interface with File Upload")
    endpoint_choice = gr.Dropdown(choices=list(endpoints.keys()), label="Select Endpoint")
    system_prompt = gr.Textbox(label="System Prompt", value="You are a helpful assistant")
    user_input = gr.Textbox(label="Your Message", placeholder="Type your message here...")
    uploaded_file = gr.File(label="Upload a File (optional)")
    output_text = gr.Textbox(label="LLM Response")
    submit = gr.Button("Send")

    submit.click(
        fn=chat_with_file,
        inputs=[endpoint_choice, system_prompt, user_input, uploaded_file],
        outputs=output_text
    )

iface.launch()