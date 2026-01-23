# kpdf

Display PDF files in the terminal using Kitty graphics protocol.

## Description

`kpdf` is a simple, non-interactive PDF viewer for the terminal that uses the Kitty graphics protocol to display PDF pages. It renders pages one after another, similar to `icat`, allowing you to view PDFs directly in your terminal without opening a separate application.

## Features

- Display specific pages or page ranges from PDF files
- Adjustable zoom levels
- Uses Kitty graphics protocol for high-quality rendering
- Non-interactive, displays pages sequentially

## Requirements

- Python 3.6+
- Kitty terminal emulator
- `pdftoppm` (from poppler-utils package)
- Optional: `pdfinfo` (from poppler-utils, for page counting)

### Installing Dependencies

On Ubuntu/Debian:
```bash
sudo apt-get install poppler-utils
```

On macOS with Homebrew:
```bash
brew install poppler
```

On Fedora/RHEL:
```bash
sudo dnf install poppler-utils
```

## Installation

```bash
pip install -e .
```

Or use directly without installation:
```bash
python3 kpdf.py [options] <pdf_file>
```

## Usage

```
kpdf [-h] [-p PAGES] [-z ZOOM] pdf_file

positional arguments:
  pdf_file              PDF file to display

optional arguments:
  -h, --help            show this help message and exit
  -p PAGES, --pages PAGES
                        Page or range of pages to display (e.g., "1", "1-3",
                        "1,3,5", "1-3,5"). Default: 1
  -z ZOOM, --zoom ZOOM  Zoom level in percent (100% = 80% of terminal width).
                        Default: 100
```

## Examples

Display the first page of a PDF:
```bash
kpdf document.pdf
```

Display pages 1 through 3:
```bash
kpdf -p 1-3 document.pdf
```

Display specific pages (1, 3, and 5):
```bash
kpdf -p 1,3,5 document.pdf
```

Display page 2 with 150% zoom:
```bash
kpdf -p 2 -z 150 document.pdf
```

Display pages 1-3 and page 5 with 75% zoom:
```bash
kpdf -p 1-3,5 -z 75 document.pdf
```

## How It Works

1. `kpdf` uses `pdftoppm` to convert PDF pages to PNG images
2. The images are sized based on the terminal width and specified zoom level
3. Images are displayed using Kitty's `icat` kitten or directly via the Kitty graphics protocol
4. Pages are displayed sequentially, one after another

## Zoom Levels

The zoom parameter controls the size of the displayed pages:
- `100` (default): Pages are rendered at 80% of terminal width
- `50`: Pages are rendered at 40% of terminal width (smaller)
- `200`: Pages are rendered at 160% of terminal width (larger)

## License

See LICENSE file for details.
