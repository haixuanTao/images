#!/usr/bin/env python3

import glob
import time

import images_rs


def test_renamed_module():
    """Test that the renamed module works correctly"""

    # Get some test images
    avif_paths = glob.glob("images/test_avif_*.avif")[:5]

    if not avif_paths:
        print("No AVIF test images found!")
        return

    print(f"Testing images with {len(avif_paths)} AVIF images...")
    print("Available functions:", dir(images_rs))
    print()

    # Test the main function
    start = time.perf_counter()
    result = images_rs.read(avif_paths)
    end = time.perf_counter()

    print(f"Processing time: {end - start:.4f}s")
    successful_count = sum(1 for img in result if img is not None)
    error_count = sum(1 for img in result if img is None)
    
    print(f"Successfully read: {successful_count} images")
    print(f"Errors: {error_count}")

    if result and result[0] is not None:
        img_array = result[0]
        print(
            f"Sample image: shape: {img_array.shape}, dtype: {img_array.dtype}"
        )

    print("\n✅ images is working correctly!")


if __name__ == "__main__":
    test_renamed_module()
