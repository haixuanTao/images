#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image
import parallel_read_avif
import glob
import concurrent.futures
import threading
from pathlib import Path
import psutil
import os

def detailed_benchmark():
    """Run detailed benchmarks with different image counts"""
    
    avif_paths = sorted(glob.glob("images/test_avif_*.avif"))
    
    print(f"System Info:")
    print(f"CPU cores: {psutil.cpu_count()} ({psutil.cpu_count(logical=False)} physical)")
    print(f"Python threads: {threading.active_count()}")
    print()
    
    # Test with different quantities
    test_sizes = [1, 3, 5, 10, 15] if len(avif_paths) >= 15 else [1, len(avif_paths)//2, len(avif_paths)]
    
    for size in test_sizes:
        if size > len(avif_paths):
            continue
            
        test_paths = avif_paths[:size]
        print(f"=== Testing with {size} AVIF images ===")
        
        # Warm up (file system cache)
        for path in test_paths:
            with Image.open(path) as img:
                pass
        
        # Test Pillow Sequential
        times = []
        for _ in range(5):  # Multiple runs for accuracy
            start = time.perf_counter()
            pillow_result = pillow_read_sequential(test_paths)
            end = time.perf_counter()
            times.append(end - start)
        pillow_seq_time = min(times)
        pillow_success = len(pillow_result['images'])
        
        # Test Pillow Threaded
        times = []
        for _ in range(5):
            start = time.perf_counter()
            pillow_thread_result = pillow_read_threaded(test_paths, max_workers=4)
            end = time.perf_counter()
            times.append(end - start)
        pillow_thread_time = min(times)
        
        # Test Rust Parallel
        times = []
        for _ in range(5):
            start = time.perf_counter()
            rust_result = parallel_read_avif.read_images_parallel(test_paths)
            end = time.perf_counter()
            times.append(end - start)
        rust_time = min(times)
        rust_success = len(rust_result['images'])
        
        print(f"Pillow Sequential: {pillow_seq_time:.4f}s ({pillow_success} images)")
        print(f"Pillow Threaded:   {pillow_thread_time:.4f}s")
        print(f"Rust Parallel:     {rust_time:.4f}s ({rust_success} images)")
        
        if pillow_seq_time > 0:
            print(f"Rust vs Pillow Sequential: {pillow_seq_time/rust_time:.2f}x")
        if pillow_thread_time > 0:
            print(f"Rust vs Pillow Threaded:   {pillow_thread_time/rust_time:.2f}x")
        print()

def pillow_read_sequential(paths):
    """Read images sequentially using Pillow"""
    results = []
    errors = []
    
    for i, path in enumerate(paths):
        try:
            with Image.open(path) as img:
                rgb_img = img.convert('RGB')
                array = np.array(rgb_img)
                results.append((array, rgb_img.size[0], rgb_img.size[1]))
        except Exception as e:
            errors.append((i, str(e)))
    
    return {"images": results, "errors": errors}

def pillow_read_threaded(paths, max_workers=None):
    """Read images using Pillow with ThreadPoolExecutor"""
    def read_single(path):
        try:
            with Image.open(path) as img:
                rgb_img = img.convert('RGB')
                return np.array(rgb_img), rgb_img.size[0], rgb_img.size[1]
        except Exception as e:
            raise e
    
    results = []
    errors = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(read_single, path): i 
                          for i, path in enumerate(paths)}
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results.append((index, result[0], result[1], result[2]))
            except Exception as e:
                errors.append((index, str(e)))
    
    # Sort results by original index
    results.sort(key=lambda x: x[0])
    final_results = [(r[1], r[2], r[3]) for r in results]
    
    return {"images": final_results, "errors": errors}

def test_overhead():
    """Test the overhead of different approaches"""
    print("=== Overhead Analysis ===")
    
    # Test Python list creation overhead
    avif_paths = sorted(glob.glob("images/test_avif_*.avif"))[:5]
    
    start = time.perf_counter()
    for _ in range(1000):
        result = parallel_read_avif.read_images_parallel([])  # Empty list
    end = time.perf_counter()
    print(f"Rust function call overhead (1000 calls): {(end-start)*1000:.4f}ms")
    
    # Test numpy array creation overhead  
    test_data = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    
    start = time.perf_counter()
    for _ in range(1000):
        arr = np.array(test_data)
    end = time.perf_counter()
    print(f"NumPy array creation overhead (1000 calls): {(end-start)*1000:.4f}ms")

if __name__ == "__main__":
    detailed_benchmark()
    test_overhead()