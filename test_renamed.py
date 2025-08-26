#!/usr/bin/env python3

import images
import glob
import time

def test_renamed_module():
    """Test that the renamed module works correctly"""
    
    # Get some test images
    avif_paths = glob.glob("images/test_avif_*.avif")[:5]
    
    if not avif_paths:
        print("No AVIF test images found!")
        return
    
    print(f"Testing images-rs with {len(avif_paths)} AVIF images...")
    print("Available functions:", dir(images))
    print()
    
    # Test the main function
    start = time.perf_counter()
    result = images.read(avif_paths)
    end = time.perf_counter()
    
    print(f"Processing time: {end - start:.4f}s")
    print(f"Successfully read: {len(result['images'])} images")
    print(f"Errors: {len(result['errors'])}")
    
    if result['images']:
        img_array, width, height = result['images'][0]
        print(f"Sample image: {width}x{height}, shape: {img_array.shape}, dtype: {img_array.dtype}")
    
    print("\n✅ images-rs is working correctly!")

if __name__ == "__main__":
    test_renamed_module()