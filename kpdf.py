#!/usr/bin/env python3
"""
kpdf - Display PDF files in terminal using Kitty graphics protocol
"""

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from typing import List, Tuple


# Kitty graphics protocol constants
KITTY_FORMAT_PNG = 100  # f=100 means PNG format
KITTY_CHUNK_SIZE = 4096  # Recommended chunk size for Kitty protocol


def get_terminal_width() -> int:
    """Get the terminal width in pixels."""
    # Try to get terminal size using kitty's method
    try:
        result = subprocess.run(
            ['kitty', '+kitten', 'icat', '--print-window-size'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout:
            # Output format: "width height" in pixels
            parts = result.stdout.strip().split()
            if len(parts) >= 1:
                return int(parts[0])
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    
    # Fallback: estimate based on character width
    # Typical terminal: 80 chars wide, ~10 pixels per char
    cols = shutil.get_terminal_size((80, 24)).columns
    return cols * 10


def parse_page_range(page_spec: str, total_pages: int) -> List[int]:
    """
    Parse page specification into list of page numbers.
    
    Examples:
        "1" -> [1]
        "1-3" -> [1, 2, 3]
        "1,3,5" -> [1, 3, 5]
        "1-3,5" -> [1, 2, 3, 5]
    
    Args:
        page_spec: Page specification string
        total_pages: Total number of pages in PDF
        
    Returns:
        List of page numbers (1-indexed)
    """
    pages = []
    
    for part in page_spec.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    
    # Filter valid page numbers
    pages = [p for p in pages if 1 <= p <= total_pages]
    
    # Remove duplicates and sort
    return sorted(set(pages))


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the total number of pages in a PDF file."""
    try:
        # Try using pdfinfo first (from poppler-utils)
        result = subprocess.run(
            ['pdfinfo', pdf_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    
    # Fallback: we'll discover pages during conversion
    # Return a large number and let the conversion filter out invalid pages
    # Note: This is a fallback only used when pdfinfo is not available
    return 9999


def pdf_to_image(pdf_path: str, page_num: int, dpi: int, output_path: str) -> bool:
    """
    Convert a PDF page to an image using pdftoppm.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed)
        dpi: Resolution in DPI
        output_path: Output image path (without extension)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use pdftoppm to convert PDF to PNG
        # -f: first page, -l: last page, -png: PNG format, -r: resolution
        subprocess.run(
            ['pdftoppm', '-f', str(page_num), '-l', str(page_num),
             '-png', '-r', str(dpi), pdf_path, output_path],
            check=True,
            capture_output=True,
            timeout=30
        )
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error converting PDF page {page_num}: {e}", file=sys.stderr)
        return False


def display_image_kitty(image_path: str):
    """
    Display an image using Kitty graphics protocol.
    
    Args:
        image_path: Path to image file
    """
    try:
        # Use kitty's icat kitten to display the image
        subprocess.run(
            ['kitty', '+kitten', 'icat', image_path],
            check=True,
            timeout=10
        )
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error displaying image: {e}", file=sys.stderr)
        
        # Fallback: try direct protocol if icat fails
        try:
            display_image_kitty_protocol(image_path)
        except Exception as fallback_e:
            print(f"Fallback also failed: {fallback_e}", file=sys.stderr)


def display_image_kitty_protocol(image_path: str):
    """
    Display an image using Kitty graphics protocol directly.
    
    Args:
        image_path: Path to image file
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Encode image data as base64
    encoded = base64.standard_b64encode(image_data).decode('ascii')
    
    # Split into chunks (Kitty protocol prefers chunks of 4096 bytes)
    chunks = [encoded[i:i+KITTY_CHUNK_SIZE] for i in range(0, len(encoded), KITTY_CHUNK_SIZE)]
    
    # Send image using Kitty graphics protocol
    # Format: ESC _G<control data>;<payload>ESC \
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk: send file info
            # a=T: transmission medium (T=direct), f=format (100=PNG), m=more data follows
            control = f"a=T,f={KITTY_FORMAT_PNG},m={1 if len(chunks) > 1 else 0}"
        elif i == len(chunks) - 1:
            # Last chunk
            control = "m=0"
        else:
            # Middle chunks
            control = "m=1"
        
        sys.stdout.write(f"\033_G{control};{chunk}\033\\")
        sys.stdout.flush()
    
    # Add newline after image
    print()


def main():
    """Main entry point for kpdf."""
    parser = argparse.ArgumentParser(
        description='Display PDF files in terminal using Kitty graphics protocol',
        epilog='Example: kpdf -p 1-3 -z 150 document.pdf'
    )
    parser.add_argument(
        'pdf_file',
        help='PDF file to display'
    )
    parser.add_argument(
        '-p', '--pages',
        default='1-10',
        help='Page or range of pages to display (e.g., "1", "1-3", "1,3,5", "1-3,5"). Default: 1-10'
    )
    parser.add_argument(
        '-z', '--zoom',
        type=float,
        default=100.0,
        help='Zoom level in percent (100%% = 80%% of terminal width). Default: 100'
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.isfile(args.pdf_file):
        print(f"Error: PDF file '{args.pdf_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Get terminal width
    terminal_width = get_terminal_width()
    
    # Calculate target width: 100% zoom = 80% of terminal width
    base_width_pixels = int(terminal_width * 0.8)
    target_width_pixels = int(base_width_pixels * args.zoom / 100.0)
    
    # Calculate DPI based on target width
    # Assume US Letter size (8.5 inches wide) as default
    # DPI = pixels / inches
    page_width_inches = 8.5
    dpi = int(target_width_pixels / page_width_inches)
    
    # Ensure reasonable DPI range
    dpi = max(72, min(dpi, 300))
    
    # Get total page count
    total_pages = get_pdf_page_count(args.pdf_file)
    
    # Parse page range
    try:
        pages = parse_page_range(args.pages, total_pages)
    except ValueError as e:
        print(f"Error: Invalid page specification '{args.pages}': {e}", file=sys.stderr)
        sys.exit(1)
    
    if not pages:
        print(f"Error: No valid pages found in range '{args.pages}'", file=sys.stderr)
        sys.exit(1)
    
    # Create temporary directory for images
    with tempfile.TemporaryDirectory() as tmpdir:
        # Process each page
        for page_num in pages:
            output_prefix = os.path.join(tmpdir, f'page_{page_num}')
            
            # Convert PDF page to image
            if not pdf_to_image(args.pdf_file, page_num, dpi, output_prefix):
                print(f"Warning: Skipping page {page_num}", file=sys.stderr)
                continue
            
            # pdftoppm adds page number suffix and extension
            # Format: output_prefix-pagenum.png where pagenum matches input page
            image_file = f"{output_prefix}-{page_num}.png"
            
            if not os.path.exists(image_file):
                print(f"Warning: Could not find generated image for page {page_num}", file=sys.stderr)
                continue
            
            # Display the image
            print(f"Page {page_num}:")
            display_image_kitty(image_file)
            print()  # Add blank line between pages


if __name__ == '__main__':
    main()
