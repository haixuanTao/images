#!/usr/bin/env python3
"""Basic tests for CI/CD pipeline"""

import images_rs
import tempfile
import os
from PIL import Image
import numpy as np

def test_import():
    """Test that the module imports successfully"""
    assert hasattr(images_rs, 'read_images_parallel')
    assert hasattr(images_rs, 'read_images_as_bytes_parallel')
    print("✅ Import test passed")

def test_empty_list():
    """Test with empty image list"""
    result = images_rs.read_images_parallel([])
    assert isinstance(result, dict)
    assert 'images' in result
    assert 'errors' in result
    assert len(result['images']) == 0
    assert len(result['errors']) == 0
    print("✅ Empty list test passed")

def test_nonexistent_files():
    """Test with non-existent files"""
    result = images_rs.read_images_parallel(['nonexistent1.png', 'nonexistent2.jpg'])
    assert len(result['images']) == 0
    assert len(result['errors']) == 2
    print("✅ Non-existent files test passed")

def test_with_real_image():
    """Test with a real generated image"""
    # Create a temporary test image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple 10x10 test image
        img_array = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img.save(tmp.name, 'PNG')
        
        try:
            # Test reading the image
            result = images_rs.read_images_parallel([tmp.name])
            
            assert len(result['images']) == 1
            assert len(result['errors']) == 0
            
            # Check the result
            loaded_array, width, height = result['images'][0]
            assert width == 10
            assert height == 10
            assert loaded_array.shape == (10, 10, 3)
            assert loaded_array.dtype == np.uint8
            
            print("✅ Real image test passed")
            
        finally:
            # Clean up
            os.unlink(tmp.name)

def test_bytes_function():
    """Test the bytes parallel function"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple test image
        img_array = np.ones((5, 5, 3), dtype=np.uint8) * 128  # Gray image
        img = Image.fromarray(img_array)
        img.save(tmp.name, 'PNG')
        
        try:
            result = images_rs.read_images_as_bytes_parallel([tmp.name])
            
            assert len(result['images']) == 1
            assert len(result['errors']) == 0
            
            # Check the result
            loaded_bytes, width, height = result['images'][0]
            assert width == 5
            assert height == 5
            assert loaded_bytes.shape == (75,)  # 5*5*3 = 75 bytes
            assert loaded_bytes.dtype == np.uint8
            
            print("✅ Bytes function test passed")
            
        finally:
            os.unlink(tmp.name)

def run_all_tests():
    """Run all tests"""
    print("Running basic tests for images-rs...")
    
    test_import()
    test_empty_list()
    test_nonexistent_files()
    test_with_real_image()
    test_bytes_function()
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    run_all_tests()