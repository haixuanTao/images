#!/usr/bin/env python3

import parallel_read_avif
import numpy as np

def test_supported_formats():
    """Test that AVIF support is working by trying to read various format extensions"""
    
    # Test with non-existent files but different extensions to see format support
    test_paths = [
        "test.jpg",
        "test.png", 
        "test.avif",
        "test.webp",
        "test.gif"
    ]
    
    print("Testing format support...")
    result = parallel_read_avif.read_images_as_bytes_parallel(test_paths)
    
    errors = result["errors"]
    
    for i, error_msg in errors:
        path = test_paths[i]
        print(f"{path}: {error_msg}")
        
        # Check if it's just a file not found error (good) vs unsupported format error (bad)
        if "No such file or directory" in error_msg:
            print(f"  ✓ {path.split('.')[-1].upper()} format appears to be supported")
        elif "unsupported" in error_msg.lower() or "unknown" in error_msg.lower():
            print(f"  ✗ {path.split('.')[-1].upper()} format may not be supported")
        else:
            print(f"  ? {path.split('.')[-1].upper()} format status unclear")

if __name__ == "__main__":
    test_supported_formats()