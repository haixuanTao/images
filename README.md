# images

[![CI](https://github.com/your-username/images/workflows/CI/badge.svg)](https://github.com/your-username/images/actions)
[![PyPI](https://img.shields.io/pypi/v/images.svg)](https://pypi.org/project/images/)
[![Python](https://img.shields.io/pypi/pyversions/images.svg)](https://pypi.org/project/images/)

A high-performance Rust-Python extension for parallel image reading with native AVIF support.

## Features

- **Parallel Processing**: Uses Rayon for concurrent image decoding
- **AVIF Support**: Native AVIF decoding with dav1d decoder
- **Multiple Formats**: PNG, JPEG, AVIF, WebP, GIF, TIFF, BMP
- **Optimized Performance**: NASM assembly optimizations where available
- **Two Output Modes**: 3D numpy arrays or flat byte arrays

## System Dependencies

### AVIF Support

This library uses the native dav1d decoder for AVIF images. You may need to install system dependencies:

**macOS (using Homebrew):**

```bash
brew install dav1d nasm
```

**Ubuntu/Debian:**

```bash
sudo apt-get install libdav1d-dev nasm
```

**Fedora/RHEL:**

```bash
sudo dnf install dav1d-devel nasm
```

### Build Requirements

- Rust toolchain
- Python 3.8+
- NASM (for optimized assembly routines)

## Installation

### From PyPI (Recommended)

```bash
pip install images
```

Pre-compiled wheels are available for:

- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Platforms**: Linux (x86_64), macOS (Intel + Apple Silicon), Windows (x86_64)

### From Source

If a wheel isn't available for your platform:

```bash
# Install system dependencies first
# macOS: brew install dav1d nasm
# Ubuntu: sudo apt-get install libdav1d-dev nasm

pip install maturin
git clone https://github.com/your-username/images
cd images
maturin develop --release
```

## Development Setup

```bash
uv sync
uv run maturin develop --release
```

## Usage

```python
import images_rs
import numpy as np

# Read images in parallel
paths = ["image1.jpg", "image2.png", "image3.avif"]
result = images_rs.read_images_as_bytes_parallel(paths)

# Access images and errors
images = result["images"]  # List of (numpy_array, width, height) tuples
errors = result["errors"]  # List of (index, error_message) tuples

for i, (img_array, width, height) in enumerate(images):
    print(f"Image {i}: {width}x{height}, shape: {img_array.shape}")
```

## Functions

### `read_images_parallel(paths)`

Returns images as 3D numpy arrays with shape `(height, width, 3)`.

**Parameters:**

- `paths`: List of image file paths

**Returns:**

- Dictionary with:
  - `"images"`: List of `(numpy_array, width, height)` tuples
  - `"errors"`: List of `(index, error_message)` tuples for failed images

### `read_images_as_bytes_parallel(paths)`

Returns images as flat byte arrays (more memory efficient).

**Parameters:**

- `paths`: List of image file paths

**Returns:**

- Dictionary with:
  - `"images"`: List of `(flat_numpy_array, width, height)` tuples
  - `"errors"`: List of `(index, error_message)` tuples for failed images

## Performance

Tested with 50 mixed-format images (PNG/JPEG/AVIF):

- **Processing speed**: ~50-57 million pixels/second
- **Average time per image**: 0.0005-0.0006 seconds
- **Parallel efficiency**: Scales with CPU cores using Rayon

## Supported Formats

- **PNG** - Full support with transparency
- **JPEG** - Standard JPEG with quality preservation
- **AVIF** - Native support via dav1d decoder with excellent compression
- **WebP** - Google's WebP format
- **GIF** - Animated GIF support (first frame)
- **TIFF** - Tagged Image File Format
- **BMP** - Windows Bitmap format
