#!/usr/bin/env python3
"""
Flask Web Application for QR Code Generator and Reader
Hosted version to use directly without installation
"""

from flask import Flask, render_template, request, send_file, jsonify, Response
from flask_cors import CORS
import os
import io
import csv
import tempfile
import uuid
import threading
import time
import json as json_module
from pathlib import Path
from werkzeug.utils import secure_filename
import qrcode
from PIL import Image
import cv2
from pyzbar import pyzbar
import zipfile
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'csv', 'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

jobs = {}
jobs_lock = threading.Lock()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _cleanup_old_jobs():
    with jobs_lock:
        expired = [
            jid for jid, job in jobs.items()
            if job.get('status') in ('completed', 'failed')
            and time.time() - job.get('finished_at', time.time()) > 3600
        ]
        for jid in expired:
            del jobs[jid]


def _run_batch_generate(job_id, csv_rows, size, format_type):
    try:
        with jobs_lock:
            jobs[job_id]['status'] = 'processing'

        total = len(csv_rows)
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, row in enumerate(csv_rows):
                try:
                    filename = secure_filename(row['filename'].strip())
                    url = row['url'].strip()

                    if not filename or not url:
                        with jobs_lock:
                            jobs[job_id]['current'] = i + 1
                        continue

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
                    zip_file.writestr(f'{filename}.{format_type}', img_io.read())
                except Exception as e:
                    logger.error(f"Error generating QR for row {i}: {e}")

                with jobs_lock:
                    jobs[job_id]['current'] = i + 1

        zip_buffer.seek(0)
        with jobs_lock:
            jobs[job_id]['result'] = zip_buffer.read()
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['finished_at'] = time.time()

    except Exception as e:
        logger.error(f"Batch generate error: {e}")
        with jobs_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['finished_at'] = time.time()


def _run_batch_read(job_id, zip_data):
    try:
        with jobs_lock:
            jobs[job_id]['status'] = 'processing'

        results = []

        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
            image_files = [
                f for f in zip_file.namelist()
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'))
            ]
            total = len(image_files)

            with jobs_lock:
                jobs[job_id]['total'] = total

            for i, img_file in enumerate(image_files):
                try:
                    image_data = zip_file.read(img_file)
                    nparr = __import__('numpy').frombuffer(image_data, __import__('numpy').uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if image is None:
                        results.append({'filename': img_file, 'qr_content': '', 'status': 'Failed to read image'})
                    else:
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        decoded_objects = pyzbar.decode(image)

                        if decoded_objects:
                            qr_data = decoded_objects[0].data.decode('utf-8')
                            results.append({'filename': img_file, 'qr_content': qr_data, 'status': 'Success'})
                        else:
                            results.append({'filename': img_file, 'qr_content': '', 'status': 'No QR code found'})
                except Exception as e:
                    results.append({'filename': img_file, 'qr_content': '', 'status': f'Error: {str(e)}'})

                with jobs_lock:
                    jobs[job_id]['current'] = i + 1

        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=['filename', 'qr_content', 'status'])
        writer.writeheader()
        writer.writerows(results)

        with jobs_lock:
            jobs[job_id]['result'] = csv_buffer.getvalue().encode('utf-8')
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['finished_at'] = time.time()

    except Exception as e:
        logger.error(f"Batch read error: {e}")
        with jobs_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['finished_at'] = time.time()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
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

        _cleanup_old_jobs()

        job_id = str(uuid.uuid4())
        with jobs_lock:
            jobs[job_id] = {
                'status': 'queued',
                'current': 0,
                'total': len(rows),
                'type': 'generate',
                'format': format_type,
                'created_at': time.time(),
            }

        thread = threading.Thread(
            target=_run_batch_generate,
            args=(job_id, rows, size, format_type),
            daemon=True
        )
        thread.start()

        return jsonify({'job_id': job_id})

    except Exception as e:
        logger.error(f"Error in batch generation: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/read-qr', methods=['POST'])
def read_qr():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Image file is required'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        image_data = file.read()
        nparr = __import__('numpy').frombuffer(image_data, __import__('numpy').uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': 'Invalid image file'}), 400

        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'ZIP file is required'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        zip_data = file.read()

        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf:
            image_files = [
                f for f in zf.namelist()
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'))
            ]

        if not image_files:
            return jsonify({'error': 'No image files found in ZIP'}), 400

        _cleanup_old_jobs()

        job_id = str(uuid.uuid4())
        with jobs_lock:
            jobs[job_id] = {
                'status': 'queued',
                'current': 0,
                'total': len(image_files),
                'type': 'read',
                'created_at': time.time(),
            }

        thread = threading.Thread(
            target=_run_batch_read,
            args=(job_id, zip_data),
            daemon=True
        )
        thread.start()

        return jsonify({'job_id': job_id})

    except Exception as e:
        logger.error(f"Error in batch reading: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/job/<job_id>/progress')
def job_progress(job_id):
    def generate():
        while True:
            with jobs_lock:
                job = jobs.get(job_id)
                if not job:
                    yield f"data: {json_module.dumps({'status': 'not_found'})}\n\n"
                    break
                snapshot = {k: v for k, v in job.items() if k != 'result'}

            yield f"data: {json_module.dumps(snapshot)}\n\n"

            if snapshot.get('status') in ('completed', 'failed'):
                break

            time.sleep(0.3)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@app.route('/api/job/<job_id>/download')
def job_download(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job.get('status') != 'completed':
        return jsonify({'error': 'Job not ready'}), 404

    result = job.get('result')
    if not result:
        return jsonify({'error': 'No result data'}), 500

    job_type = job.get('type', 'generate')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if job_type == 'generate':
        format_type = job.get('format', 'png')
        return send_file(
            io.BytesIO(result),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'qr_codes_{timestamp}.zip'
        )
    else:
        return send_file(
            io.BytesIO(result),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'qr_results_{timestamp}.csv'
        )


@app.route('/api/download-example-csv', methods=['GET'])
def download_example_csv():
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
