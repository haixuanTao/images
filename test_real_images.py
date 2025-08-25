#!/usr/bin/env python3

import parallel_read_avif
import numpy as np
import time

def test_with_real_images():
    """Test the parallel image reading with real downloaded images"""
    
    # Test with our actual images
    test_paths = [
        "test_generated.png",
        "test_red.png", 
        "test_generated.avif"
    ]
    
    print("Testing with real images...")
    print(f"Testing paths: {test_paths}")
    print()
    
    # Test the 3D array function
    print("=== Testing read_images_parallel (returns 3D numpy arrays) ===")
    start_time = time.time()
    result = parallel_read_avif.read_images_parallel(test_paths)
    end_time = time.time()
    
    print(f"Processing time: {end_time - start_time:.4f} seconds")
    
    images = result["images"]
    errors = result["errors"]
    
    print(f"Successfully read: {len(images)} images")
    print(f"Errors: {len(errors)}")
    print()
    
    for i, (img_array, width, height) in enumerate(images):
        print(f"Image {i} ({test_paths[i]}):")
        print(f"  - Dimensions: {width}x{height}")
        print(f"  - Array shape: {img_array.shape}")
        print(f"  - Array dtype: {img_array.dtype}")
        print(f"  - Min/Max values: {img_array.min()}/{img_array.max()}")
        print(f"  - Sample pixel values: {img_array[0, 0, :] if img_array.shape[0] > 0 else 'N/A'}")
        print()
    
    for i, error_msg in errors:
        print(f"Error reading {test_paths[i]}: {error_msg}")
        print()
    
    print("=== Testing read_images_as_bytes_parallel (returns flat byte arrays) ===")
    start_time = time.time()
    result2 = parallel_read_avif.read_images_as_bytes_parallel(test_paths)
    end_time = time.time()
    
    print(f"Processing time: {end_time - start_time:.4f} seconds")
    
    images2 = result2["images"]
    errors2 = result2["errors"]
    
    print(f"Successfully read: {len(images2)} images")
    print(f"Errors: {len(errors2)}")
    print()
    
    for i, (img_array, width, height) in enumerate(images2):
        print(f"Image {i} ({test_paths[i]}):")
        print(f"  - Dimensions: {width}x{height}")
        print(f"  - Array shape: {img_array.shape}")
        print(f"  - Array dtype: {img_array.dtype}")
        print(f"  - Expected total bytes: {width * height * 3}")
        print(f"  - Actual array size: {img_array.size}")
        print(f"  - Sample values: {img_array[:6] if len(img_array) > 6 else img_array}")
        print()
    
    for i, error_msg in errors2:
        print(f"Error reading {test_paths[i]}: {error_msg}")
        print()
    
    # Verify AVIF specifically
    if len(images) > 0 or len(images2) > 0:
        avif_found = False
        for i, path in enumerate(test_paths):
            if path.endswith('.avif'):
                if i < len(images) and images[i]:
                    print("🎉 AVIF support confirmed! Successfully read AVIF image.")
                    avif_found = True
                elif i < len(errors) and any(err[0] == i for err in errors):
                    error = next(err[1] for err in errors if err[0] == i)
                    print(f"❌ AVIF reading failed: {error}")
        
        if not avif_found and any(path.endswith('.avif') for path in test_paths):
            print("⚠️  AVIF file was in test list but not successfully processed")

if __name__ == "__main__":
    test_with_real_images()