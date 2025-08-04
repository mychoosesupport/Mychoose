from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfMerger
import os
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('merge.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('files')
    merger = PdfMerger()

    for file in files:
        if file.filename.endswith('.pdf'):
            merger.append(file)

    merged_pdf = BytesIO()
    merger.write(merged_pdf)
    merger.close()
    merged_pdf.seek(0)

    return send_file(merged_pdf, download_name="merged.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
