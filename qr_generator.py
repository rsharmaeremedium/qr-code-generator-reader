#!/usr/bin/env python3
"""
Optimized QR Code Generator
Generates QR codes from URLs with CSV mapping support
"""

import os
import sys
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
import qrcode
from qrcode.image.pure import PyPNGImage
from PIL import Image
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QRCodeGenerator:
    """
    Optimized QR Code Generator with batch processing capabilities
    """
    
    def __init__(self, output_dir: str = "qr_codes", size: int = 500, file_format: str = "png", max_workers: int = 8):
        """
        Initialize QR Code Generator
        
        Args:
            output_dir: Output directory for QR codes
            size: Size of QR code in pixels (default: 500)
            file_format: File format - 'png' or 'jpg' (default: png)
            max_workers: Number of concurrent workers for generation (default: 8)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.size = size
        self.file_format = file_format.lower()
        self.max_workers = max_workers
        
        if self.file_format not in ['png', 'jpg', 'jpeg']:
            raise ValueError("File format must be 'png' or 'jpg'")
        
        if self.file_format == 'jpeg':
            self.file_format = 'jpg'
        
        logger.info(f"QR Generator initialized: {self.output_dir} | Size: {self.size}px | Format: {self.file_format}")
    
    def _generate_single_qr(self, url: str, filename: str) -> Tuple[bool, str]:
        """
        Generate a single QR code
        
        Args:
            url: URL to encode in QR code
            filename: Output filename without extension
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create QR code with optimized settings
            qr = qrcode.QRCode(
                version=None,  # Auto-detect version
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
                box_size=1,  # Minimal box size, will scale via PIL
                border=2,  # Minimal border
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create image with specified size
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize to target size
            img = img.resize((self.size, self.size), Image.Resampling.LANCZOS)
            
            # Save file
            output_path = self.output_dir / f"{filename}.{self.file_format}"
            
            if self.file_format == 'jpg':
                # Convert RGBA to RGB for JPG
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    rgb_img.save(output_path, quality=95, optimize=True)
                else:
                    img.save(output_path, quality=95, optimize=True)
            else:
                img.save(output_path, optimize=True)
            
            return True, f"Generated: {output_path}"
        
        except Exception as e:
            return False, f"Error generating QR for '{filename}': {str(e)}"
    
    def generate_from_csv(self, csv_file: str) -> dict:
        """
        Generate QR codes from CSV file
        CSV format: filename, url
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Dictionary with generation statistics
        """
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        # Read CSV file
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'filename' in row and 'url' in row:
                    filename = row['filename'].strip()
                    url = row['url'].strip()
                    if filename and url:
                        data.append((url, filename))
        
        if not data:
            raise ValueError("No valid data found in CSV file")
        
        if len(data) > 5000:
            logger.warning(f"Large batch detected: {len(data)} QR codes. Processing with {self.max_workers} workers.")
        
        logger.info(f"Starting generation of {len(data)} QR codes...")
        
        # Generate QR codes in parallel
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._generate_single_qr, url, filename): (url, filename) 
                      for url, filename in data}
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Generating QR codes"):
                url, filename = futures[future]
                success, message = future.result()
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(message)
        
        # Log results
        logger.info(f"\nGeneration Complete!")
        logger.info(f"Success: {results['success']}")
        logger.info(f"Failed: {results['failed']}")
        
        if results['errors']:
            logger.warning(f"Errors encountered:")
            for error in results['errors'][:10]:  # Show first 10 errors
                logger.warning(error)
        
        return results
    
    def generate_single(self, url: str, filename: str) -> bool:
        """
        Generate a single QR code
        
        Args:
            url: URL to encode
            filename: Output filename without extension
            
        Returns:
            Success status
        """
        success, message = self._generate_single_qr(url, filename)
        logger.info(message)
        return success


def main():
    """
    Main CLI interface for QR code generation
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate QR codes from CSV file')
    parser.add_argument('csv_file', help='CSV file with columns: filename, url')
    parser.add_argument('-o', '--output', default='qr_codes', help='Output directory (default: qr_codes)')
    parser.add_argument('-s', '--size', type=int, default=500, help='QR code size in pixels (default: 500)')
    parser.add_argument('-f', '--format', choices=['png', 'jpg'], default='png', help='Output format (default: png)')
    parser.add_argument('-w', '--workers', type=int, default=8, help='Number of concurrent workers (default: 8)')
    
    args = parser.parse_args()
    
    try:
        generator = QRCodeGenerator(
            output_dir=args.output,
            size=args.size,
            file_format=args.format,
            max_workers=args.workers
        )
        
        results = generator.generate_from_csv(args.csv_file)
        
        if results['failed'] == 0:
            logger.info(f"\n✓ All {results['success']} QR codes generated successfully!")
            sys.exit(0)
        else:
            logger.warning(f"\n✗ Generation completed with {results['failed']} errors")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
