#!/usr/bin/env python3

import images_rs
import numpy as np
import time

def test_parallel_read():
    # Create some test image paths (you'll need actual images to test)
    paths = [
        "test1.jpg", 
        "test2.png", 
        "test3.avif"
    ]
    
    print("Testing parallel image reading...")
    
    start_time = time.time()
    result = images_rs.read_images_as_bytes_parallel(paths)
    end_time = time.time()
    
    print(f"Read {len(paths)} images in {end_time - start_time:.2f} seconds")
    
    images = result["images"]
    errors = result["errors"]
    
    print(f"Successfully read: {len(images)} images")
    print(f"Errors: {len(errors)}")
    
    for i, (img_array, width, height) in enumerate(images):
        print(f"Image {i}: {width}x{height}, shape: {img_array.shape}, dtype: {img_array.dtype}")
    
    for i, error_msg in errors:
        print(f"Error reading image {i}: {error_msg}")

if __name__ == "__main__":
    test_parallel_read()