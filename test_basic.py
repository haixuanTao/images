#!/usr/bin/env python3
"""Basic tests for CI/CD pipeline"""

import os
import tempfile

import numpy as np
from PIL import Image

import images_rs


def test_import():
    """Test that the module imports successfully"""
    assert hasattr(images_rs, "read")
    print("✅ Import test passed")


def test_empty_list():
    """Test with empty image list"""
    result = images_rs.read([])
    assert isinstance(result, list)
    assert len(result) == 0
    print("✅ Empty list test passed")


def test_nonexistent_files():
    """Test with non-existent files"""
    result = images_rs.read(["nonexistent1.png", "nonexistent2.jpg"])
    assert len(result) == 2
    assert result[0] is None
    assert result[1] is None
    print("✅ Non-existent files test passed")


def test_with_real_image():
    """Test with a real generated image"""
    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a simple 10x10 test image
        img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img.save(tmp.name, "PNG")

        try:
            # Test reading the image
            result = images_rs.read([tmp.name])

            assert len(result) == 1
            assert result[0] is not None

            # Check the result
            loaded_array = result[0]
            assert loaded_array.shape == (10, 10, 3)
            assert loaded_array.dtype == np.uint8

            print("✅ Real image test passed")

        finally:
            # Clean up
            os.unlink(tmp.name)


def test_thread_parameter():
    """Test the num_threads parameter"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a simple test image
        img_array = np.ones((5, 5, 3), dtype=np.uint8) * 128  # Gray image
        img = Image.fromarray(img_array)
        img.save(tmp.name, "PNG")

        try:
            # Test with specific thread count
            result = images_rs.read([tmp.name], num_threads=1)

            assert len(result) == 1
            assert result[0] is not None
            assert result[0].shape == (5, 5, 3)

            print("✅ Thread parameter test passed")

        finally:
            os.unlink(tmp.name)


def test_image_content():
    """Test that the actual pixel values are read correctly"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a test image with known pixel values
        # Red, Green, Blue stripes
        img_array = np.zeros((3, 3, 3), dtype=np.uint8)
        img_array[0, :, 0] = 255  # Red stripe
        img_array[1, :, 1] = 255  # Green stripe  
        img_array[2, :, 2] = 255  # Blue stripe
        
        img = Image.fromarray(img_array)
        img.save(tmp.name, "PNG")

        try:
            # Read the image back
            result = images_rs.read([tmp.name])
            
            assert len(result) == 1
            assert result[0] is not None
            
            loaded_array = result[0]
            assert loaded_array.shape == (3, 3, 3)
            
            # Check specific pixel values
            # Red stripe (row 0)
            assert loaded_array[0, 0, 0] == 255  # Red channel
            assert loaded_array[0, 0, 1] == 0    # Green channel
            assert loaded_array[0, 0, 2] == 0    # Blue channel
            
            # Green stripe (row 1)  
            assert loaded_array[1, 0, 0] == 0    # Red channel
            assert loaded_array[1, 0, 1] == 255  # Green channel
            assert loaded_array[1, 0, 2] == 0    # Blue channel
            
            # Blue stripe (row 2)
            assert loaded_array[2, 0, 0] == 0    # Red channel
            assert loaded_array[2, 0, 1] == 0    # Green channel  
            assert loaded_array[2, 0, 2] == 255  # Blue channel

            print("✅ Image content validation test passed")

        finally:
            os.unlink(tmp.name)


def run_all_tests():
    """Run all tests"""
    print("Running basic tests for images...")

    test_import()
    test_empty_list()
    test_nonexistent_files()
    test_with_real_image()
    test_thread_parameter()
    test_image_content()

    print("🎉 All tests passed!")


if __name__ == "__main__":
    run_all_tests()
