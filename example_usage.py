#!/usr/bin/env python3
"""
Example usage of QR Code Generator and Reader
"""

from qr_generator import QRCodeGenerator
from qr_reader import QRCodeReader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_generate():
    """
    Example: Generate QR codes from CSV
    """
    logger.info("=" * 50)
    logger.info("EXAMPLE 1: Generate QR Codes from CSV")
    logger.info("=" * 50)
    
    # Initialize generator
    generator = QRCodeGenerator(
        output_dir='qr_codes',
        size=500,
        file_format='png',
        max_workers=8
    )
    
    # Generate from CSV
    results = generator.generate_from_csv('example_input.csv')
    logger.info(f"\nGeneration Results:")
    logger.info(f"  Success: {results['success']}")
    logger.info(f"  Failed: {results['failed']}")
    
    return results

def example_generate_single():
    """
    Example: Generate a single QR code
    """
    logger.info("\n" + "=" * 50)
    logger.info("EXAMPLE 2: Generate Single QR Code")
    logger.info("=" * 50)
    
    generator = QRCodeGenerator(output_dir='qr_codes', size=500)
    
    # Generate single QR code
    success = generator.generate_single(
        'https://www.python.org',
        'Python_Org'
    )
    logger.info(f"Generation: {'Success' if success else 'Failed'}")

def example_read():
    """
    Example: Read QR codes from folder
    """
    logger.info("\n" + "=" * 50)
    logger.info("EXAMPLE 3: Read QR Codes from Folder")
    logger.info("=" * 50)
    
    # Initialize reader
    reader = QRCodeReader(max_workers=8)
    
    # Read from folder
    results = reader.read_from_folder(
        './qr_codes',
        'qr_results.csv'
    )
    
    logger.info(f"\nReading Results:")
    logger.info(f"  Success: {results['success']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Output: qr_results.csv")
    
    # Print first few results
    if results['data']:
        logger.info(f"\nFirst few results:")
        for item in results['data'][:3]:
            logger.info(f"  {item['filename']}: {item['qr_content']}")

def example_read_single():
    """
    Example: Read a single QR code
    """
    logger.info("\n" + "=" * 50)
    logger.info("EXAMPLE 4: Read Single QR Code")
    logger.info("=" * 50)
    
    reader = QRCodeReader()
    
    # Read single image
    qr_content = reader.read_single('./qr_codes/Google.png')
    if qr_content:
        logger.info(f"Decoded: {qr_content}")
    else:
        logger.info("No QR code found or error reading image")

if __name__ == '__main__':
    try:
        # Run examples
        example_generate()
        example_generate_single()
        example_read()
        example_read_single()
        
        logger.info("\n" + "=" * 50)
        logger.info("All examples completed successfully!")
        logger.info("=" * 50)
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.info("Make sure 'example_input.csv' exists and run from the correct directory.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
