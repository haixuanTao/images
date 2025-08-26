#!/usr/bin/env python3

import images
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
    result = images.read(paths, num_threads=4)
    end_time = time.time()
    
    print(f"Read {len(paths)} images in {end_time - start_time:.2f} seconds")
    
    successful_count = sum(1 for img in result if img is not None)
    error_count = sum(1 for img in result if img is None)
    
    print(f"Successfully read: {successful_count} images")
    print(f"Errors: {error_count}")
    
    for i, img_array in enumerate(result):
        if img_array is not None:
            print(f"Image {i}: shape: {img_array.shape}, dtype: {img_array.dtype}")
        else:
            print(f"Image {i}: Failed to load (check stderr for error details)")

if __name__ == "__main__":
    test_parallel_read()