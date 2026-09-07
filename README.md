# QR Code Generator & Reader

An optimized, high-performance Python solution for generating and reading QR codes at scale. Perfect for batch processing up to 5000+ QR codes efficiently.

## 🚀 Quick Deploy

### Deploy to Heroku (Easiest!)

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/rsharmaeremedium/qr-code-generator-reader)

### Deploy to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/Z_p1Mj?referralCode=railway)

### Deploy to Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect this GitHub repo
4. Deploy

## Features

### 🎯 QR Code Generator
- **Batch Processing**: Generate thousands of QR codes efficiently
- **CSV Support**: Read URLs and filenames from CSV file
- **Customizable Output**: 
  - Size: Up to 500px (or any size)
  - Format: PNG or JPG
  - Output Directory: Specify any location
- **Parallel Processing**: Concurrent generation with configurable workers
- **High Quality**: LANCZOS resampling for crisp QR codes
- **Error Handling**: Robust error tracking and reporting
- **Progress Tracking**: Real-time progress bar with tqdm

### 📖 QR Code Reader
- **Batch Reading**: Scan QR codes from entire folders
- **Multi-Format Support**: PNG, JPG, BMP, GIF, TIFF
- **CSV Export**: Generate detailed report with filenames and decoded content
- **Parallel Processing**: Fast concurrent reading
- **Error Logging**: Track successful and failed reads

### 🌐 Web Interface
- Beautiful, responsive UI
- Generate single QR codes
- Batch generate from CSV
- Read single QR codes
- Batch read from ZIP files
- Download results instantly

## Installation & Setup

### Requirements
- Python 3.8+
- pip

### Local Installation

```bash
# Clone the repository
git clone https://github.com/rsharmaeremedium/qr-code-generator-reader.git
cd qr-code-generator-reader

# Install dependencies
pip install -r requirements.txt
```

### Run Web Application Locally

```bash
# Install web dependencies
pip install -r requirements_web.txt

# Run the Flask app
python app.py

# Open browser and visit
# http://localhost:5000
```

### Run with Docker

```bash
# Build image
docker build -t qr-code-app .

# Run container
docker run -p 5000:5000 qr-code-app

# Visit http://localhost:5000
```

## Usage

### 1. Generate QR Codes from CSV (CLI)

#### Prepare CSV File
Create a CSV file with two columns: `filename` and `url`

```csv
filename,url
Google,https://www.google.com
GitHub,https://www.github.com
Stack Overflow,https://stackoverflow.com
```

#### Generate QR Codes

**Basic usage:**
```bash
python qr_generator.py example_input.csv
```

**Advanced options:**
```bash
python qr_generator.py example_input.csv \
  -o qr_codes \
  -s 500 \
  -f png \
  -w 12
```

**Options:**
- `-o, --output`: Output directory (default: `qr_codes`)
- `-s, --size`: QR code size in pixels (default: `500`)
- `-f, --format`: Output format - `png` or `jpg` (default: `png`)
- `-w, --workers`: Number of concurrent workers (default: `8`)

#### Output
Generated QR codes will be saved as:
- `qr_codes/Google.png`
- `qr_codes/GitHub.png`
- `qr_codes/Stack Overflow.png`
- etc.

### 2. Read QR Codes from Folder (CLI)

#### Read QR codes

**Basic usage:**
```bash
python qr_reader.py ./qr_codes
```

**Advanced options:**
```bash
python qr_reader.py ./qr_codes \
  -o qr_results.csv \
  -w 12
```

**Options:**
- `-o, --output`: Output CSV file (default: `qr_codes_output.csv`)
- `-w, --workers`: Number of concurrent workers (default: `8`)

#### Output
Generated CSV file (`qr_codes_output.csv`):
```csv
filename,qr_content,status
Google.png,https://www.google.com,Success
GitHub.png,https://www.github.com,Success
Stack Overflow.png,https://stackoverflow.com,Success
```

### 3. Use Web Interface

#### Access the Web App
- **Online (Deployed)**: Get URL after deployment
- **Local**: `http://localhost:5000`

#### Features
- **Generate Single**: Enter URL → Download QR code
- **Generate Batch**: Upload CSV → Download ZIP with all QR codes
- **Read Single**: Upload image → Get decoded URL
- **Read Batch**: Upload ZIP → Download CSV with results

## Python API Usage

### Generate QR Codes Programmatically

```python
from qr_generator import QRCodeGenerator

# Initialize generator
generator = QRCodeGenerator(
    output_dir='qr_codes',
    size=500,
    file_format='png',
    max_workers=8
)

# Generate from CSV
results = generator.generate_from_csv('example_input.csv')
print(f"Success: {results['success']}, Failed: {results['failed']}")

# Or generate single QR code
generator.generate_single('https://example.com', 'example')
```

### Read QR Codes Programmatically

```python
from qr_reader import QRCodeReader

# Initialize reader
reader = QRCodeReader(max_workers=8)

# Read from folder
results = reader.read_from_folder('./qr_codes', 'output.csv')
print(f"Success: {results['success']}, Failed: {results['failed']}")

# Or read single image
qr_content = reader.read_single('./qr_codes/Google.png')
print(f"Decoded: {qr_content}")
```

## API Endpoints (Web)

### Generate Single QR
```
POST /api/generate-qr
Content-Type: application/json

{
  "url": "https://example.com",
  "size": 500,
  "format": "png"
}

Response: PNG/JPG image file
```

### Generate Batch QR
```
POST /api/generate-batch
Content-Type: multipart/form-data

file: CSV file
size: 500 (optional)
format: png (optional)

Response: ZIP file with QR codes
```

### Read Single QR
```
POST /api/read-qr
Content-Type: multipart/form-data

file: Image file

Response:
{
  "success": true,
  "data": "https://example.com"
}
```

### Read Batch QR
```
POST /api/read-batch
Content-Type: multipart/form-data

file: ZIP file with images

Response: CSV file with results
```

## Performance

### Benchmark Results (Typical)

**Generation:**
- 100 QR codes: ~2-3 seconds
- 500 QR codes: ~8-12 seconds
- 1000 QR codes: ~15-20 seconds
- 5000 QR codes: ~60-90 seconds

**Reading:**
- 100 QR codes: ~3-5 seconds
- 500 QR codes: ~10-15 seconds
- 1000 QR codes: ~20-30 seconds
- 5000 QR codes: ~90-150 seconds

*Note: Performance varies based on hardware and worker count. More workers = faster processing (with diminishing returns after 8-16 workers).*

## Optimization Tips

1. **Increase Workers**: For large batches, increase `--workers` to 12-16 (if CPU cores available)
   ```bash
   python qr_generator.py input.csv -w 16
   ```

2. **JPG Format**: For slightly faster generation and smaller file sizes
   ```bash
   python qr_generator.py input.csv -f jpg
   ```

3. **Batch Processing**: Process multiple CSVs sequentially for memory efficiency

4. **SSD Storage**: Use SSD for faster I/O operations

## File Structure

```
.
├── app.py                      # Flask web application
├── qr_generator.py             # QR code generation module
├── qr_reader.py                # QR code reading module
├── requirements.txt            # CLI dependencies
├── requirements_web.txt        # Web dependencies
├── templates/
│   └── index.html              # Web UI
├── Dockerfile                  # Docker configuration
├── Procfile                    # Heroku configuration
├── app.json                    # Heroku app.json
├── example_input.csv           # Example input CSV
├── example_usage.py            # Example usage script
└── README.md                   # This file
```

## Deployment Options

### Heroku (Recommended)
1. Click the "Deploy to Heroku" button above
2. Or use CLI:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   heroku open
   ```

### Railway
1. Click the "Deploy on Railway" button above
2. Or visit [railway.app](https://railway.app)

### Render
1. Visit [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Deploy

### Docker
```bash
docker build -t qr-code-app .
docker run -p 5000:5000 qr-code-app
```

## Error Handling

Both tools include comprehensive error handling:

- **Invalid URLs**: Skipped with error logging
- **Corrupted Images**: Skipped with error reporting
- **File Permission Errors**: Caught and reported
- **Missing Files**: Clear error messages

Check the logs for detailed error information:

```bash
# Enable debug logging (modify logging level in code to DEBUG)
# Error details are saved during processing
```

## Troubleshooting

### Issue: `ModuleNotFoundError`
**Solution:** Ensure all dependencies are installed
```bash
pip install -r requirements.txt
# For web app
pip install -r requirements_web.txt
```

### Issue: Slow Performance
**Solution:** 
- Increase worker count: `-w 16`
- Use JPG format instead of PNG
- Move to SSD storage
- Check CPU availability

### Issue: No QR codes found when reading
**Solution:**
- Ensure image format is supported (.png, .jpg, .bmp, .gif, .tiff)
- Verify QR codes are not corrupted
- Check image brightness/contrast
- Try increasing DPI or resolution of images

### Issue: Port already in use (local)
**Solution:**
```bash
python app.py --port 5001
```

## Dependencies

### CLI
- **qrcode[pil]**: QR code generation
- **pillow**: Image processing
- **opencv-python**: Image reading and processing
- **pyzbar**: QR code decoding
- **pandas**: Data handling
- **numpy**: Numerical operations
- **tqdm**: Progress bars

### Web
- **flask**: Web framework
- **flask-cors**: CORS support
- **gunicorn**: Production WSGI server
- All CLI dependencies

## License

MIT License - Feel free to use this project for personal and commercial purposes.

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Changelog

### v2.0.0 (Web Edition)
- ✅ Flask web application
- ✅ Beautiful responsive UI
- ✅ Deploy to Heroku, Railway, Render
- ✅ Docker support
- ✅ REST API endpoints
- ✅ Batch file upload/download

### v1.0.0 (Initial Release)
- ✅ Optimized QR code generator with batch processing
- ✅ High-performance QR code reader
- ✅ CSV input/output support
- ✅ Parallel processing with configurable workers
- ✅ Support for PNG and JPG formats
- ✅ Customizable QR code sizes
- ✅ Comprehensive error handling
- ✅ Progress tracking with tqdm
