import os
import email
import base64
import re
import json
import fitz  # PyMuPDF for PDFs
import pytesseract  # OCR for images
from PIL import Image
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser
from docx import Document
from google import genai
import shutil
from dotenv import load_dotenv
from EmailClassificationDB import EmailClassificationModel, request_type_json_to_string
from db_init import get_db
import time
import tempfile


load_dotenv()
db = get_db()
email_classification_model = EmailClassificationModel(db)

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD")  # install tesseract-ocr and set the path in .env

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # Set the GEMINI_API_KEY in .env
# LLM Placeholder Function
def analyze_with_llm(email_body, request_types):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"""Can you please extract the following details of this service request which was extracted from a mail chain with details of attachments and its contents appended {email_body}  in following json format - 
        {{
          "request_type": "string", // one of the request types listed below
          "sub_request_type": "string", // one of the sub request types listed below that belongs to the request type
          "from": "string", // email address of the last sender
          "to": "string",   // email address of the last recipient
          "subject": "string", // subject of the email
          "customer_name": "string" // the customer name for whom the service request is created
          "last_date": "string", // latest date of conversation in YYYY-MM-DD format
          "urgency": "string", // Low, Medium, High, Critical
          "shortened_description": "string",
          "confidence_score": number, // 0-100 value indicating confidence
          "reason": "string", // key data which helped make this classification
          "secondary_intent": "string" // If your confidence score is > 90 for 2 or more request types, mention it here, else leave it blank.
        }}

        The request and sub request types are listed below:
        REQUEST_TYPES = {request_types}
        
        Do not give any additional information other than the JSON Requested above.
     """
    )
    print(response.text)
    output = response.text
    parsed_output = extract_and_parse_json(response.text)
    if parsed_output is not None:
        output = parsed_output
    print(output)
    return output


def extract_and_parse_json(input_string):
    # Remove leading and trailing markdown code block markers if present
    json_str = input_string.strip()
    if json_str.startswith("```json"):
        json_str = json_str[len("```json"):].strip()
    if json_str.endswith("```"):
        json_str = json_str[:-len("```")].strip()

    # Normalize line endings (handle both \n and \r\n)
    json_str = json_str.replace('\r\n', '\n')

    try:
        # Parse the cleaned JSON string
        json_data = json.loads(json_str)
        return json_data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


def extract_text_from_docx(docx_path):
    """Extract text from a Word (.docx) document."""
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs]).strip()
    os.remove(docx_path)  # Delete file after reading
    return text


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text") + "\n"
    doc.close()
    os.remove(pdf_path)
    return text.strip()


def extract_text_from_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    image.close()
    os.remove(image_path)
    return text.strip()

def extract_text_from_txt(txt_file):
    """Extract text from a TXT file."""
    text = txt_file.read().decode('utf-8').strip()
    return text

def extract_text_from_pdf_bytes(pdf_bytes):
    """Extract text from PDF bytes using PyMuPDF."""
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_text_from_docx_bytes(docx_bytes):
    """Extract text from DOCX bytes."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(docx_bytes)
        tmp_path = tmp.name
    text = extract_text_from_docx(tmp_path)
    return text

def extract_text_from_txt_bytes(txt_bytes):
    """Extract text from TXT bytes."""
    text = txt_bytes.decode('utf-8').strip()
    return text


def process_eml_file(eml_path, output_dir):
    """Process an .eml file from a file path, extract content and attachments."""
    with open(eml_path, "rb") as f:
        msg = f.read()

        email_chain, full_text = extract_email_chain_and_attachments(msg, output_dir)

        request_types = email_classification_model.get_all_request_types()
        request_types = request_type_json_to_string(request_types)
        json_data = analyze_with_llm(email_chain, request_types)
        json_data['extracted_texts'] = email_chain
        json_data['email_file_name'] = eml_path

    return json_data


def extract_email_chain_with_llm(full_text):
    """
    Uses the LLM to extract an email chain from the given full_text.
    The LLM is instructed to return a JSON array where each element has:
    {
        "type": "email",
        "from": "email address or sender name",
        "to": "email address or recipient name",
        "subject": "email subject",
        "time": "email sent time",
        "body": "body of the email"
    }
    """
    prompt = f"""
    The following text contains an email conversation with multiple replies.
    Please extract the conversation into a JSON array where each element is an object representing one email message.
    Each object must have the following keys:
    - "type": which should always be "email"
    - "from": the sender's email address or name
    - "to": the recipient's email address or name
    - "subject": the email subject
    - "time": the sent time of the email
    - "body": the email body text

    If any field is not available, use an empty string.
    Return only the JSON array, nothing else.

    The text is:
    {full_text}
    """
    # Call the LLM extraction function with the prompt.

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt)
    output = response.text
    parsed_output = extract_and_parse_json(output)
    if parsed_output is not None:
        output = parsed_output
    # Expecting the LLM to return a JSON array.
    return output


def extract_email_chain_and_attachments(eml_bytes, attachment_dir):
    """
    Process an .eml file given as bytes.
    Saves attachments to the specified attachment_dir.
    Returns a tuple: (final_extracted_json, full_raw_text)
    """
    print(f"Processing email with {len(eml_bytes)} bytes")
    msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)

    # Prefer the HTML part for chain extraction.
    html_body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_body = part.get_payload(decode=True).decode(errors="ignore")
            if html_body:
                break

    if html_body:
        # Convert the HTML to text. You might use BeautifulSoup to remove tags.
        soup = BeautifulSoup(html_body, "html.parser")
        full_text = soup.get_text(separator="\n").strip()
        # Use the LLM to extract the email chain as a JSON array.
        email_chain = extract_email_chain_with_llm(full_text)
        # At this point, email_chain should be a JSON array (or a string that you can parse as JSON).
        # Optionally, if needed, add header fields from the email to the first element.
        try:
            import json
            if isinstance(email_chain, str):
                email_chain = json.loads(email_chain)
            if email_chain and isinstance(email_chain, list):
                # Fill in header details for the first message if missing.
                email_chain[0]["from"] = msg.get("From", "")
                email_chain[0]["to"] = msg.get("To", "")
                email_chain[0]["subject"] = msg.get("Subject", "")
                email_chain[0]["time"] = msg.get("Date", "")
        except Exception as e:
            print(f"Error parsing LLM output: {e}")
            email_chain = [{
                "type": "email",
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "time": msg.get("Date", ""),
                "body": full_text
            }]
    else:
        # Fallback to plain text extraction.
        plain_text = ""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                plain_text = part.get_payload(decode=True).decode(errors="ignore")
                if plain_text:
                    break
        full_text = plain_text
        email_chain = [{
            "type": "email",
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "subject": msg.get("Subject", ""),
            "time": msg.get("Date", ""),
            "body": plain_text
        }]

    # Process attachments and append each as a separate element in the email chain.
    os.makedirs(attachment_dir, exist_ok=True)
    attachment_texts = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if filename:
                temp_filepath = os.path.join(temp_dir, filename)
                with open(temp_filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                dest_filepath = os.path.join(attachment_dir, filename)
                shutil.move(temp_filepath, dest_filepath)
                attachment_text = ""
                if filename.lower().endswith(".pdf"):
                    attachment_text = extract_text_from_pdf(dest_filepath)
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    attachment_text = extract_text_from_image(dest_filepath)
                elif filename.lower().endswith(".txt"):
                    with open(dest_filepath, "r", encoding="utf-8") as f:
                        attachment_text = extract_text_from_txt(f)
                    os.remove(dest_filepath)
                elif filename.lower().endswith(".docx"):
                    attachment_text = extract_text_from_docx(dest_filepath)
                # Append the attachment as a separate element.
                attachment_json = {
                    "type": "attachment",
                    "attachment_name": filename,
                    "attachment_content": attachment_text
                }
                email_chain.append(attachment_json)
                attachment_texts.append(attachment_text)

    return email_chain, full_text



def process_eml_folder(input_folder, output_folder, archive_folder, attachment_directory):
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(archive_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.endswith(".eml"):
            eml_path = os.path.join(input_folder, filename)
            json_result = process_eml_file(eml_path, attachment_directory)
            json_output_path = os.path.join(output_folder, filename.replace(".eml", ".json"))
            with open(json_output_path, "w", encoding="utf-8") as json_file:
                json.dump(json_result, json_file, indent=4)
            shutil.move(eml_path, os.path.join(archive_folder, filename))


# For folder-based processing (if needed)
if __name__ == "__main__":
    input_directory = "../resources"
    output_directory = "../output"
    archive_directory = "../resources/archive"
    attachment_directory = "../attachments"
    os.makedirs(attachment_directory, exist_ok=True)
    process_eml_folder(input_directory, output_directory, archive_directory, attachment_directory)

