import os
import requests
import fitz  # PyMuPDF
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import io
import json

# --- Configuration ---
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = os.path.expanduser('~/Desktop/summary-api/summaries')  # Output folder
OLLAMA_API_URL = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'llama3'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    extracted_text = ""
    try:
        doc = fitz.open(pdf_path)
        print(f"Processing PDF with {len(doc)} pages.")

        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            if page_text.strip():
                extracted_text += page_text + "\n"
                print(f"Page {page_num + 1}: Extracted text directly.")
            else:
                print(f"Page {page_num + 1}: No text found, attempting OCR.")
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                try:
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text.strip():
                        extracted_text += ocr_text + "\n"
                        print(f"Page {page_num + 1}: Extracted text via OCR.")
                    else:
                        print(f"Page {page_num + 1}: OCR did not yield any text.")
                except Exception as e:
                    print(f"Error during OCR on page {page_num + 1}: {e}")
        doc.close()
    except Exception as e:
        print(f"An error occurred during PDF processing: {e}")
        return None
    return extracted_text

def summarize_text_with_llama3(text_content):
    if not text_content or not text_content.strip():
        print("Cannot summarize empty content.")
        return None

    print("Sending content to Ollama for summarization...")
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": f"Please provide a concise summary of the following text:\n\n---\n\n{text_content}\n\n---\n\nSummary:",
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        summary = response.json().get('response', '').strip()
        print("Successfully received summary from Ollama.")
        return summary
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama API: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during summarization: {e}")
        return None

def save_summary_to_file(documentID, output_data):
    """Helper function to save summary data to JSON file"""
    output_filename = f"{documentID}.json"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Summary saved to '{output_path}'")
    return output_path

@app.route('/summarize', methods=['POST'])
def summarize_pdf_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Get new required parameters from form-data
    apiFunction = request.form.get("apiFunction")
    documentID = request.form.get("documentID")
    dataSearchField = request.form.get("dataSearchField")
    dataField = request.form.get("dataField")

    if not apiFunction:
        return jsonify({"error": "Missing apiFunction parameter"}), 400
    if not documentID:
        return jsonify({"error": "Missing documentID parameter"}), 400
    if not dataSearchField:
        return jsonify({"error": "Missing dataSearchField parameter"}), 400
    if not dataField:
        return jsonify({"error": "Missing dataField parameter"}), 400

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.lower().endswith('.pdf'):
        filename = file.filename
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(pdf_path)
        print(f"File '{filename}' uploaded successfully.")

        extracted_content = extract_text_from_pdf(pdf_path)
        if not extracted_content:
            return jsonify({"error": "Could not extract any text from the PDF."}), 500

        summary = summarize_text_with_llama3(extracted_content)
        if not summary:
            return jsonify({"error": "Failed to generate summary. Is Ollama running?"}), 500

        # Create output JSON with new structure
        output_data = {
            "documentID": documentID,
            "DataSearchField": dataSearchField,
            "DataField": dataField,
            "apiFunction": apiFunction,
            "summary": summary
        }
      
        # Save to file
        output_path = save_summary_to_file(documentID, output_data)

        return jsonify({
            "message": "File processed successfully.",
            "input_file": filename,
            "summary_file": output_path,
            "summary_content": summary,
        })

    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

@app.route('/test-save', methods=['POST'])
def test_save_endpoint():
    """
    Test endpoint to save dummy data to a JSON file for testing purposes.
    Accepts parameters via query string.
    """
    # Get parameters from query string
    apiFunction = request.args.get("apiFunction")
    documentID = request.args.get("documentID")
    dataSearchField = request.args.get("dataSearchField")
    dataField = request.args.get("dataField")
    summary = request.args.get("summary", "This is a test summary for testing purposes.")

    # Validate required parameters
    if not apiFunction:
        return jsonify({"error": "Missing apiFunction parameter"}), 400
    if not documentID:
        return jsonify({"error": "Missing documentID parameter"}), 400
    if not dataSearchField:
        return jsonify({"error": "Missing dataSearchField parameter"}), 400
    if not dataField:
        return jsonify({"error": "Missing dataField parameter"}), 400

    # Create output JSON data
    output_data = {
        "documentID": documentID,
        "DataSearchField": dataSearchField,
        "DataField": dataField,
        "apiFunction": apiFunction,
        "summary": summary 
    }

    # Save to file using helper function
    try:
        output_path = save_summary_to_file(documentID, output_data)
        
        return jsonify({
            "message": "Test data saved successfully.",
            "output_file": output_path,
            "data": output_data
        })
    except Exception as e:
        print(f"Error saving test data: {e}")
        return jsonify({"error": "Failed to save test data."}), 500

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)