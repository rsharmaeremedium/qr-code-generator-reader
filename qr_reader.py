#!/usr/bin/env python3
"""
Optimized QR Code Reader
Scans QR codes from images in a folder and generates CSV report
"""

import os
import sys
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional
import cv2
from pyzbar import pyzbar
from PIL import Image
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QRCodeReader:
    """
    Optimized QR Code Reader with batch processing capabilities
    """
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    
    def __init__(self, max_workers: int = 8):
        """
        Initialize QR Code Reader
        
        Args:
            max_workers: Number of concurrent workers for reading (default: 8)
        """
        self.max_workers = max_workers
        logger.info(f"QR Reader initialized with {max_workers} workers")
    
    def _read_single_qr(self, image_path: Path) -> Tuple[str, Optional[str], str]:
        """
        Read QR code from a single image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (filename, decoded_data, status_message)
        """
        filename = image_path.name
        
        try:
            # Try reading with OpenCV first (faster)
            image = cv2.imread(str(image_path))
            
            if image is None:
                # Fallback to PIL if OpenCV fails
                try:
                    image = cv2.cvtColor(
                        cv2.imread(str(image_path), cv2.IMREAD_COLOR),
                        cv2.COLOR_BGR2GRAY
                    )
                except:
                    return filename, None, f"Failed to read image: {filename}"
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect and decode QR code
            decoded_objects = pyzbar.decode(image)
            
            if decoded_objects:
                # Get first QR code found
                qr_data = decoded_objects[0].data.decode('utf-8')
                return filename, qr_data, "Success"
            else:
                return filename, None, f"No QR code found: {filename}"
        
        except Exception as e:
            return filename, None, f"Error reading '{filename}': {str(e)}"
    
    def read_from_folder(self, folder_path: str, output_csv: str = "qr_codes_output.csv") -> dict:
        """
        Read QR codes from all images in a folder
        
        Args:
            folder_path: Path to folder containing images
            output_csv: Output CSV filename
            
        Returns:
            Dictionary with reading statistics
        """
        folder = Path(folder_path)
        
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find all supported image files
        image_files = []
        for ext in self.SUPPORTED_FORMATS:
            image_files.extend(folder.glob(f"*{ext}"))
            image_files.extend(folder.glob(f"*{ext.upper()}"))
        
        if not image_files:
            raise ValueError(f"No image files found in {folder_path}")
        
        # Remove duplicates
        image_files = list(set(image_files))
        logger.info(f"Found {len(image_files)} image files")
        
        # Read QR codes in parallel
        results = {'success': 0, 'failed': 0, 'data': []}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._read_single_qr, img): img 
                      for img in image_files}
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Reading QR codes"):
                filename, qr_data, status = future.result()
                
                if qr_data:
                    results['success'] += 1
                    results['data'].append({
                        'filename': filename,
                        'qr_content': qr_data,
                        'status': status
                    })
                else:
                    results['failed'] += 1
                    results['data'].append({
                        'filename': filename,
                        'qr_content': '',
                        'status': status
                    })
        
        # Write to CSV
        try:
            with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['filename', 'qr_content', 'status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(results['data'])
            
            logger.info(f"\nResults saved to: {output_csv}")
        except Exception as e:
            logger.error(f"Error writing CSV: {e}")
            return results
        
        # Log statistics
        logger.info(f"\nReading Complete!")
        logger.info(f"Total files scanned: {len(image_files)}")
        logger.info(f"QR codes read successfully: {results['success']}")
        logger.info(f"Failed to read: {results['failed']}")
        
        return results
    
    def read_single(self, image_path: str) -> Optional[str]:
        """
        Read QR code from a single image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Decoded QR code content or None
        """
        filename, qr_data, status = self._read_single_qr(Path(image_path))
        logger.info(status)
        return qr_data


def main():
    """
    Main CLI interface for QR code reading
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Read QR codes from images in a folder')
    parser.add_argument('folder', help='Folder containing QR code images')
    parser.add_argument('-o', '--output', default='qr_codes_output.csv', help='Output CSV file (default: qr_codes_output.csv)')
    parser.add_argument('-w', '--workers', type=int, default=8, help='Number of concurrent workers (default: 8)')
    
    args = parser.parse_args()
    
    try:
        reader = QRCodeReader(max_workers=args.workers)
        results = reader.read_from_folder(args.folder, args.output)
        
        if results['failed'] == 0:
            logger.info(f"\n✓ All {results['success']} QR codes read successfully!")
            sys.exit(0)
        else:
            logger.warning(f"\n✗ Reading completed with {results['failed']} errors")
            sys.exit(0)  # Exit 0 even with partial failures
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
