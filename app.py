#!/usr/bin/env python3
"""
Flask Web Application for QR Code Generator and Reader
Hosted version to use directly without installation
"""

from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import os
import io
import csv
import tempfile
from pathlib import Path
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image
import cv2
from pyzbar import pyzbar
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'csv', 'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    """Generate single QR code"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        size = int(data.get('size', 500))
        format_type = data.get('format', 'png').lower()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if size < 100 or size > 2000:
            return jsonify({'error': 'Size must be between 100 and 2000 pixels'}), 400
        
        if format_type not in ['png', 'jpg']:
            return jsonify({'error': 'Format must be png or jpg'}), 400
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_io = io.BytesIO()
        if format_type == 'jpg':
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                rgb_img.save(img_io, format='JPEG', quality=95, optimize=True)
            else:
                img.save(img_io, format='JPEG', quality=95, optimize=True)
        else:
            img.save(img_io, format='PNG', optimize=True)
        
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype=f'image/{format_type}',
            as_attachment=True,
            download_name=f'qrcode.{format_type}'
        )
    
    except Exception as e:
        logger.error(f"Error generating QR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-batch', methods=['POST'])
def generate_batch():
    """Generate QR codes from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'CSV file is required'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be CSV format'}), 400
        
        size = int(request.form.get('size', 500))
        format_type = request.form.get('format', 'png').lower()
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode('utf8'), newline=None)
        reader = csv.DictReader(stream)
        
        rows = []
        for row in reader:
            if 'filename' in row and 'url' in row:
                rows.append(row)
        
        if not rows:
            return jsonify({'error': 'CSV must have filename and url columns'}), 400
        
        if len(rows) > 5000:
            return jsonify({'error': 'Maximum 5000 QR codes per batch'}), 400
        
        # Create ZIP with QR codes
        import zipfile
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            success_count = 0
            failed_count = 0
            errors = []
            
            for row in rows:
                try:
                    filename = secure_filename(row['filename'].strip())
                    url = row['url'].strip()
                    
                    if not filename or not url:
                        failed_count += 1
                        continue
                    
                    # Generate QR
                    qr = qrcode.QRCode(
                        version=None,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=1,
                        border=2,
                    )
                    qr.add_data(url)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    
                    # Save to ZIP
                    img_io = io.BytesIO()
                    if format_type == 'jpg':\n                        if img.mode in ('RGBA', 'LA', 'P'):
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            rgb_img.save(img_io, format='JPEG', quality=95, optimize=True)
                        else:
                            img.save(img_io, format='JPEG', quality=95, optimize=True)
                    else:
                        img.save(img_io, format='PNG', optimize=True)
                    
                    img_io.seek(0)
                    zip_file.writestr(f'{filename}.{format_type}', img_io.read())
                    success_count += 1
                
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{row.get('filename', 'unknown')}: {str(e)}")
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'qr_codes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        )
    
    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/read-qr', methods=['POST'])
def read_qr():
    """Read QR code from image"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Image file is required'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read image
        image_data = file.read()
        nparr = __import__('numpy').frombuffer(image_data, __import__('numpy').uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Invalid image file'}), 400
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Decode QR
        decoded_objects = pyzbar.decode(image)
        
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode('utf-8')
            return jsonify({'success': True, 'data': qr_data})
        else:
            return jsonify({'success': False, 'error': 'No QR code found in image'}), 404
    
    except Exception as e:
        logger.error(f"Error reading QR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/read-batch', methods=['POST'])
def read_batch():
    """Read QR codes from ZIP of images"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'ZIP file is required'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        import zipfile
        
        results = []
        
        with zipfile.ZipFile(file, 'r') as zip_file:
            for img_file in zip_file.namelist():
                if not img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
                    continue
                
                try:
                    image_data = zip_file.read(img_file)
                    nparr = __import__('numpy').frombuffer(image_data, __import__('numpy').uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if image is None:
                        results.append({'filename': img_file, 'qr_content': '', 'status': 'Failed to read image'})
                        continue
                    
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    decoded_objects = pyzbar.decode(image)
                    
                    if decoded_objects:
                        qr_data = decoded_objects[0].data.decode('utf-8')
                        results.append({'filename': img_file, 'qr_content': qr_data, 'status': 'Success'})
                    else:
                        results.append({'filename': img_file, 'qr_content': '', 'status': 'No QR code found'})\n                \n                except Exception as e:
                    results.append({'filename': img_file, 'qr_content': '', 'status': f'Error: {str(e)}'})\n        
        # Create CSV response
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=['filename', 'qr_content', 'status'])
        writer.writeheader()
        writer.writerows(results)
        
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        return send_file(
            io.BytesIO(csv_bytes),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'qr_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        logger.error(f"Error in batch reading: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-example-csv', methods=['GET'])
def download_example_csv():
    """Download example CSV template"""
    csv_content = """filename,url
Google,https://www.google.com
GitHub,https://www.github.com
Stack Overflow,https://stackoverflow.com
Python Docs,https://docs.python.org
Mozilla MDN,https://developer.mozilla.org
"""
    return send_file(
        io.BytesIO(csv_content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='example_input.csv'
    )

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large (max 100MB)'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
