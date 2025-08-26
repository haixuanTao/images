#!/usr/bin/env python3

import images
import numpy as np
import time
import os
import glob

def test_all_images():
    """Test parallel reading with all 50 generated images"""
    
    # Get all test images
    image_paths = sorted(glob.glob("images/test_*.png") + 
                        glob.glob("images/test_*.jpg") + 
                        glob.glob("images/test_*.avif"))
    
    print(f"Found {len(image_paths)} test images")
    print(f"Images: {image_paths[:5]}..." if len(image_paths) > 5 else f"Images: {image_paths}")
    print()
    
    # Test both functions
    functions_to_test = [
        ("read_images_parallel", "3D numpy arrays"),
        ("read_images_as_bytes_parallel", "flat byte arrays")
    ]
    
    working_images = []
    broken_images = []
    
    for func_name, description in functions_to_test:
        print(f"=== Testing {func_name} ({description}) ===")
        
        start_time = time.time()
        func = getattr(images, func_name)
        result = func(image_paths)
        end_time = time.time()
        
        images = result["images"]
        errors = result["errors"]
        
        print(f"Processing time: {end_time - start_time:.4f} seconds")
        print(f"Successfully read: {len(images)} images")
        print(f"Errors: {len(errors)}")
        print(f"Average time per image: {(end_time - start_time) / len(image_paths):.4f} seconds")
        print()
        
        # Track working and broken images
        if func_name == "read_images_parallel":  # Only need to check once
            working_paths = set(image_paths)
            for error_idx, error_msg in errors:
                broken_path = image_paths[error_idx]
                broken_images.append((broken_path, error_msg))
                working_paths.discard(broken_path)
            working_images = list(working_paths)
        
        # Show detailed info for first few images
        print("Sample successful images:")
        for i, (img_array, width, height) in enumerate(images[:5]):
            path = image_paths[i] if i < len(image_paths) else f"image_{i}"
            print(f"  {path}: {width}x{height}, shape: {img_array.shape}, dtype: {img_array.dtype}")
        
        if len(images) > 5:
            print(f"  ... and {len(images) - 5} more images")
        print()
        
        # Show errors
        if errors:
            print("Errors encountered:")
            for error_idx, error_msg in errors:
                error_path = image_paths[error_idx]
                print(f"  {error_path}: {error_msg}")
            print()
        
        # Performance stats
        if images:
            total_pixels = sum(width * height for _, width, height in images)
            print(f"Total pixels processed: {total_pixels:,}")
            pixels_per_second = total_pixels / (end_time - start_time)
            print(f"Processing speed: {pixels_per_second:,.0f} pixels/second")
            print()
        
        print("-" * 60)
        print()
    
    # Summary
    print("=== SUMMARY ===")
    print(f"Total images tested: {len(image_paths)}")
    print(f"Working images: {len(working_images)}")
    print(f"Broken images: {len(broken_images)}")
    print()
    
    if working_images:
        # Count by format
        format_counts = {}
        for path in working_images:
            ext = path.split('.')[-1].lower()
            format_counts[ext] = format_counts.get(ext, 0) + 1
        
        print("Working images by format:")
        for fmt, count in sorted(format_counts.items()):
            print(f"  {fmt.upper()}: {count} images")
        print()
    
    if broken_images:
        print("Broken images to remove:")
        for path, error in broken_images:
            print(f"  {path}: {error}")
        print()
        
        # Remove broken images
        print("Removing broken images...")
        for path, error in broken_images:
            try:
                os.remove(path)
                print(f"  Removed: {path}")
            except Exception as e:
                print(f"  Failed to remove {path}: {e}")
        print()
    else:
        print("🎉 All images are working perfectly!")
    
    return working_images, broken_images

if __name__ == "__main__":
    working, broken = test_all_images()
    
    if broken:
        print(f"Test completed. Removed {len(broken)} broken images.")
        print(f"Remaining {len(working)} working images ready for use.")
    else:
        print(f"Test completed successfully with all {len(working)} images working!")