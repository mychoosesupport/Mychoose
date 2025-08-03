from flask import Flask, request, send_file, render_template, jsonify
from pdf2docx import Converter
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from docx import Document
import os
import time
import shutil

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def pdf_to_word(pdf_path, docx_path, start_page=None, end_page=None):
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=start_page or 0, end=end_page)
        cv.close()
        return True, "Conversion successful"
    except Exception as e:
        return False, str(e)

def pdf_to_word_ocr(pdf_path, docx_path):
    try:
        images = convert_from_path(pdf_path)
        doc = Document()
        for image in images:
            text = pytesseract.image_to_string(image, lang='eng')
            doc.add_paragraph(text)
        doc.save(docx_path)
        return True, "OCR conversion successful"
    except Exception as e:
        return False, str(e)

def batch_pdf_to_word(pdf_folder, output_folder, use_ocr=False, start_page=None, end_page=None):
    results = []
    output_files = []
    for pdf_file in os.listdir(pdf_folder):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            docx_path = os.path.join(output_folder, pdf_file.replace(".pdf", ".docx"))
            if use_ocr:
                success, message = pdf_to_word_ocr(pdf_path, docx_path)
            else:
                success, message = pdf_to_word(pdf_path, docx_path, start_page, end_page)
            results.append({"file": pdf_file, "success": success, "message": message})
            if success:
                output_files.append(docx_path)
    return results, output_files

def secure_delete_files(*file_paths):
    for path in file_paths:
        if os.path.exists(path):
            os.remove(path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files")
        use_ocr = request.form.get("use_ocr") == "on"
        start_page = request.form.get("start_page")
        end_page = request.form.get("end_page")
        start_page = int(start_page) if start_page else None
        end_page = int(end_page) if end_page else None

        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
        shutil.rmtree(OUTPUT_FOLDER, ignore_errors=True)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)

        for file in files:
            if file and file.filename.endswith(".pdf"):
                file.save(os.path.join(UPLOAD_FOLDER, file.filename))

        results, output_files = batch_pdf_to_word(UPLOAD_FOLDER, OUTPUT_FOLDER, use_ocr, start_page, end_page)

        if len(output_files) == 1:
            response = send_file(output_files[0], as_attachment=True)
            time.sleep(10)
            secure_delete_files(*[os.path.join(UPLOAD_FOLDER, f.filename) for f in files], *output_files)
            return response
        elif len(output_files) > 1:
            zip_path = os.path.join(OUTPUT_FOLDER, "converted_files.zip")
            shutil.make_archive(os.path.join(OUTPUT_FOLDER, "converted_files"), 'zip', OUTPUT_FOLDER)
            response = send_file(zip_path, as_attachment=True)
            time.sleep(10)
            secure_delete_files(*[os.path.join(UPLOAD_FOLDER, f.filename) for f in files], *output_files, zip_path)
            return response
        else:
            return jsonify({"results": results}), 400

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
