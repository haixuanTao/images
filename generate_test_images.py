#!/usr/bin/env python3

import numpy as np
from PIL import Image
import os

def create_test_images():
    """Generate 50 test images in various formats"""
    
    # Create images directory if it doesn't exist
    os.makedirs("images", exist_ok=True)
    
    # Remove existing test images to start fresh
    for f in os.listdir("images"):
        if f.startswith("test_"):
            os.remove(os.path.join("images", f))
    
    image_paths = []
    
    # Generate 20 PNG images
    for i in range(20):
        # Create random colored images of different sizes
        width = 50 + (i * 10) % 200  # Vary width from 50 to 250
        height = 50 + (i * 15) % 200  # Vary height from 50 to 250
        
        # Create different patterns
        if i % 4 == 0:
            # Random noise
            arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        elif i % 4 == 1:
            # Solid colors
            color = [i * 10 % 256, (i * 20) % 256, (i * 30) % 256]
            arr = np.full((height, width, 3), color, dtype=np.uint8)
        elif i % 4 == 2:
            # Gradient
            arr = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                arr[y, :, 0] = (y * 255) // height
                arr[y, :, 1] = ((height - y) * 255) // height
                arr[y, :, 2] = 128
        else:
            # Checkerboard pattern
            arr = np.zeros((height, width, 3), dtype=np.uint8)
            for y in range(height):
                for x in range(width):
                    if (x // 10 + y // 10) % 2:
                        arr[y, x] = [255, 255, 255]
                    else:
                        arr[y, x] = [0, 0, 0]
        
        img = Image.fromarray(arr)
        path = f"images/test_png_{i:02d}.png"
        img.save(path)
        image_paths.append(path)
        print(f"Generated {path} ({width}x{height})")
    
    # Generate 15 JPEG images
    for i in range(15):
        width = 100 + (i * 20) % 300
        height = 100 + (i * 25) % 300
        
        # Create vibrant patterns for JPEG
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                arr[y, x, 0] = (x * 255) // width
                arr[y, x, 1] = (y * 255) // height
                arr[y, x, 2] = ((x + y) * 255) // (width + height)
        
        img = Image.fromarray(arr)
        path = f"images/test_jpeg_{i:02d}.jpg"
        img.save(path, "JPEG", quality=85)
        image_paths.append(path)
        print(f"Generated {path} ({width}x{height})")
    
    # Generate 15 AVIF images (convert some PNGs to AVIF)
    try:
        for i in range(15):
            width = 80 + (i * 15) % 150
            height = 80 + (i * 18) % 150
            
            # Create smooth gradients (good for AVIF compression)
            arr = np.zeros((height, width, 3), dtype=np.uint8)
            center_x, center_y = width // 2, height // 2
            
            for y in range(height):
                for x in range(width):
                    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    max_dist = np.sqrt(center_x**2 + center_y**2)
                    
                    arr[y, x, 0] = int(255 * (dist / max_dist)) if max_dist > 0 else 0
                    arr[y, x, 1] = int(255 * (1 - dist / max_dist)) if max_dist > 0 else 255
                    arr[y, x, 2] = int(128 + 127 * np.sin(dist / 10))
            
            img = Image.fromarray(arr)
            path = f"images/test_avif_{i:02d}.avif"
            img.save(path, "AVIF", quality=80)
            image_paths.append(path)
            print(f"Generated {path} ({width}x{height})")
    except Exception as e:
        print(f"AVIF generation failed for some images: {e}")
        print("This might be due to pillow-avif not being installed or configured properly")
    
    return image_paths

if __name__ == "__main__":
    paths = create_test_images()
    print(f"\nGenerated {len(paths)} test images total")
    print("Image generation completed!")