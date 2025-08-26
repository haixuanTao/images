#!/usr/bin/env python3
"""Basic tests for CI/CD pipeline"""

import images
import tempfile
import os
from PIL import Image
import numpy as np

def test_import():
    """Test that the module imports successfully"""
    assert hasattr(images, 'read')
    print("✅ Import test passed")

def test_empty_list():
    """Test with empty image list"""
    result = images.read([])
    assert isinstance(result, list)
    assert len(result) == 0
    print("✅ Empty list test passed")

def test_nonexistent_files():
    """Test with non-existent files"""
    result = images.read(['nonexistent1.png', 'nonexistent2.jpg'])
    assert len(result) == 2
    assert result[0] is None
    assert result[1] is None
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
            result = images.read([tmp.name])
            
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
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple test image
        img_array = np.ones((5, 5, 3), dtype=np.uint8) * 128  # Gray image
        img = Image.fromarray(img_array)
        img.save(tmp.name, 'PNG')
        
        try:
            # Test with specific thread count
            result = images.read([tmp.name], num_threads=1)
            
            assert len(result) == 1
            assert result[0] is not None
            assert result[0].shape == (5, 5, 3)
            
            print("✅ Thread parameter test passed")
            
        finally:
            os.unlink(tmp.name)

def run_all_tests():
    """Run all tests"""
    print("Running basic tests for images-rs...")
    
    test_import()
    test_empty_list()
    test_nonexistent_files()
    test_with_real_image()
    test_thread_parameter()
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    run_all_tests()