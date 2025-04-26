import streamlit as st
import json
import pdfplumber
from paddleocr import PaddleOCR
import requests
import io
import os
from fpdf import FPDF

# Function to extract text from PDF
def extract_pdf_text(pdf_file):
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text()
    return extracted_text

# Function to extract text using PaddleOCR (optional, fallback)
def extract_text_with_ocr(pdf_file):
    ocr = PaddleOCR(use_angle_cls=True, lang='en') 
    img = pdf_file
    result = ocr.ocr(img, cls=True)
    text = ""
    for line in result[0]:
        text += line[1][0] + "\n"
    return text

# Function to auto-fill fields using Hugging Face API (GPT model)
def autofill_with_ai(user_profile, form_fields):
    url = "https://api-inference.huggingface.co/models/distilgpt2"
    
    prompt = f"""
    You are an intelligent assistant. Given the following form fields and user profile, please map the profile data to the fields.
    
    Form fields: {form_fields}
    User profile: {json.dumps(user_profile, indent=2)}
    
    Return the result as a JSON object like:
    {{
        "Full Name": "John Doe",
        "Date of Birth": "1990-01-01",
        "Address": "123 Street, City",
        "Email": "john@example.com"
    }}
    """
    
    response = requests.post(
        url,
        headers={"Authorization": "Bearer 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"},
        json={"inputs": prompt}
    )
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to generate the filled PDF
def generate_filled_pdf(filled_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for field, value in filled_data.items():
        pdf.cell(200, 10, txt=f"{field}: {value}", ln=True)

    output_filename = "filled_form.pdf"
    pdf.output(output_filename)
    return output_filename

# Streamlit UI
st.title("LLM-Powered PDF Form Filler")
st.markdown("### Upload a PDF form to auto-fill it with your profile data")

pdf_file = st.file_uploader("Choose a PDF form", type=["pdf"])

if pdf_file is not None:
    st.subheader("Extracted PDF Text:")
    extracted_text = extract_pdf_text(pdf_file)
    st.text_area("PDF Content", extracted_text, height=300)
    
    st.subheader("Parsed Basic User Info:")
    user_profile = {
        "Full Name": "Vikash Sharma",
        "Email": "vikash@example.com",
        "Phone Number": "9876543210",
        "Address": "123 ABC Street, Dehradun",
        "Education": "Bachelor of Technology, Computer Science"
    }
    st.json(user_profile)

    form_fields = ["Full Name", "Email", "Phone Number", "Address", "Education"]

    if st.button("Auto-Fill Using AI"):
        try:
            llm_output = autofill_with_ai(user_profile, form_fields)
            st.subheader("🧠 AI Output:")
            st.code(llm_output, language='json')

            try:
                filled_data = json.loads(llm_output)
                st.subheader("Filled Data:")
                st.json(filled_data)
            except Exception as e:
                st.warning(f"Could not parse LLM output correctly: {e}")
                st.subheader("Using Extracted Data:")
                st.json(user_profile)
        
        except Exception as e:
            st.error(f"Error calling AI model: {e}")

    st.subheader("Editable Form")
    filled_data = user_profile
    for field in form_fields:
        filled_data[field] = st.text_input(field, filled_data.get(field, ''))
    
    if st.button("Generate and Download Filled PDF"):
        output_filename = generate_filled_pdf(filled_data)
        with open(output_filename, "rb") as pdf_file:
            st.download_button(
                label="Download Filled PDF",
                data=pdf_file,
                file_name=output_filename,
                mime="application/pdf"
            )
        os.remove(output_filename)
