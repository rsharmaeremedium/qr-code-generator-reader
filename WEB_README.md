# QR Code Generator & Reader - Web Edition

## Now Hosted Online! 🚀

This web application allows you to generate and read QR codes directly from your browser.

### Deploy to Heroku

#### Quick Deploy Button

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/rsharmaeremedium/qr-code-generator-reader)

#### Manual Deployment

```bash
# 1. Install Heroku CLI
# Visit: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login to Heroku
heroku login

# 3. Create a new app
heroku create your-app-name

# 4. Deploy
git push heroku main

# 5. Open app
heroku open
```

### Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Connect your repository
5. Select this repository
6. Click "Deploy"

### Deploy to Render

1. Go to [Render.com](https://render.com)
2. Click "New +"
3. Select "Web Service"
4. Connect your GitHub repository
5. Configure:
   - Name: `qr-code-app`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements_web.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
6. Click "Create Web Service"

### Run Locally

```bash
# 1. Install dependencies
pip install -r requirements_web.txt

# 2. Run the app
python app.py

# 3. Open browser
# Visit: http://localhost:5000
```

## Features

### 🎯 Generate Single QR Code
- Enter any URL
- Customize size (100-2000 pixels)
- Choose format (PNG or JPG)
- Download instantly

### 🎯 Generate Batch QR Codes
- Upload CSV file with URLs
- Generate up to 5000 QR codes at once
- Download all as ZIP file
- Supports PNG and JPG formats

### 📖 Read Single QR Code
- Upload image containing QR code
- Instantly decodes the content
- Supports PNG, JPG, BMP, GIF, TIFF

### 📖 Read Batch QR Codes
- Upload ZIP with multiple QR code images
- Reads all QR codes automatically
- Downloads CSV with results

## CSV Format

### For Generation (Input)
```csv
filename,url
Google,https://www.google.com
GitHub,https://www.github.com
Stack Overflow,https://stackoverflow.com
```

### For Reading (Output)
```csv
filename,qr_content,status
Google.png,https://www.google.com,Success
GitHub.png,https://www.github.com,Success
```

## Docker

```bash
# Build image
docker build -t qr-code-app .

# Run container
docker run -p 5000:5000 qr-code-app

# Open browser
# Visit: http://localhost:5000
```

## Performance

- Single QR generation: < 1 second
- Batch generation (100): 2-3 seconds
- Batch generation (1000): 15-20 seconds
- Batch generation (5000): 60-90 seconds
- Single QR reading: < 1 second
- Batch reading (100): 3-5 seconds

## Troubleshooting

### Issue: Module not found
**Solution:** Ensure all dependencies are installed
```bash
pip install -r requirements_web.txt
```

### Issue: Port already in use
**Solution:** Use a different port
```bash
python app.py --port 5001
```

### Issue: File too large
**Limit:** Maximum 100MB per file

## API Endpoints

### Generate Single QR
```
POST /api/generate-qr
Body: {
  "url": "https://example.com",
  "size": 500,
  "format": "png"
}
Response: PNG/JPG image file
```

### Generate Batch QR
```
POST /api/generate-batch
Body: multipart/form-data
  - file: CSV file
  - size: pixels (default: 500)
  - format: png or jpg (default: png)
Response: ZIP file with QR codes
```

### Read Single QR
```
POST /api/read-qr
Body: multipart/form-data
  - file: Image file
Response: JSON with decoded content
{
  "success": true,
  "data": "https://example.com"
}
```

### Read Batch QR
```
POST /api/read-batch
Body: multipart/form-data
  - file: ZIP file with images
Response: CSV file with results
```

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **QR Generation:** qrcode, Pillow
- **QR Reading:** OpenCV, pyzbar
- **Deployment:** Heroku, Railway, Render, Docker

## Support

For issues and questions, please open an issue on GitHub.

## License

MIT License - Feel free to use this project!
