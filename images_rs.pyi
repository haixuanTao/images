"""Type stubs for images_rs - A fast parallel image reading library.

This module provides high-performance image reading capabilities using Rust's
image processing libraries with Python bindings. It supports multiple image
formats and leverages parallel processing for optimal performance.
"""

from typing import List, Optional, Union
import numpy as np

def read(
    paths: List[Union[str, "os.PathLike[str]"]], 
    num_threads: Optional[int] = None
) -> List[Optional[np.ndarray]]:
    """Read multiple images in parallel and return them as numpy arrays.
    
    This function efficiently reads multiple image files concurrently using Rust's
    high-performance image processing libraries. It supports various formats including
    PNG, JPEG, AVIF, WebP, GIF, TIFF, and BMP.
    
    Args:
        paths: List of file paths to image files. Can be strings or Path-like objects.
            Supports both absolute and relative paths.
        num_threads: Optional number of threads to use for parallel processing.
            If None, uses the default thread pool size. Note that the global thread
            pool can only be initialized once per process - subsequent calls with
            different num_threads will be ignored.
    
    Returns:
        List of numpy arrays with shape (height, width, 3) representing RGB images.
        Failed reads return None at the corresponding index. The returned arrays
        have dtype uint8 with values in the range [0, 255].
    
    Raises:
        ValueError: If there are issues with array shape conversion.
        TypeError: If paths contains invalid types.
        
    Note:
        - Images are automatically converted to RGB format regardless of input format
        - The function uses fast format detection based on file extensions
        - If extension-based detection fails, it falls back to content-based detection
        - Failed image reads are returned as None rather than raising exceptions
        - The function is optimized for batch processing of multiple images
        
    Example:
        >>> import images_rs
        >>> images = images_rs.read(['photo1.jpg', 'photo2.png', 'photo3.avif'])
        >>> print(f"Loaded {len([img for img in images if img is not None])} images")
        >>> if images[0] is not None:
        ...     print(f"First image shape: {images[0].shape}")
    """
    ...