#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image
import parallel_read_avif
import concurrent.futures
import glob
import shutil
import os

def create_large_test_set():
    """Create a larger test set by duplicating existing images"""
    
    base_avifs = sorted(glob.glob("images/test_avif_*.avif"))[:5]  # Use first 5 as templates
    
    # Create large_test directory
    os.makedirs("large_test", exist_ok=True)
    
    # Clean existing files
    for f in glob.glob("large_test/*.avif"):
        os.remove(f)
    
    # Create 100 test images by duplicating the base ones
    large_test_paths = []
    for i in range(100):
        source = base_avifs[i % len(base_avifs)]
        dest = f"large_test/stress_test_{i:03d}.avif"
        shutil.copy2(source, dest)
        large_test_paths.append(dest)
    
    print(f"Created {len(large_test_paths)} test images for stress testing")
    return large_test_paths

def pillow_sequential(paths):
    """Pillow sequential reading"""
    results = []
    start = time.perf_counter()
    
    for path in paths:
        try:
            with Image.open(path) as img:
                rgb_img = img.convert('RGB')
                array = np.array(rgb_img)
                results.append((array, rgb_img.size[0], rgb_img.size[1]))
        except Exception as e:
            print(f"Error reading {path}: {e}")
    
    end = time.perf_counter()
    return results, end - start

def pillow_threaded(paths, max_workers=4):
    """Pillow with ThreadPoolExecutor"""
    def read_single(path):
        try:
            with Image.open(path) as img:
                rgb_img = img.convert('RGB')
                return np.array(rgb_img), rgb_img.size[0], rgb_img.size[1]
        except Exception as e:
            raise Exception(f"Error reading {path}: {e}")
    
    results = []
    start = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(read_single, path): path for path in paths}
        
        for future in concurrent.futures.as_completed(future_to_path):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")
    
    end = time.perf_counter()
    return results, end - start

def rust_parallel(paths):
    """Our Rust parallel implementation"""
    start = time.perf_counter()
    result = parallel_read_avif.read_images_parallel(paths)
    end = time.perf_counter()
    
    return result['images'], end - start

def stress_test():
    """Run stress test with different batch sizes"""
    
    print("Creating large test dataset...")
    large_paths = create_large_test_set()
    
    # Test different batch sizes
    batch_sizes = [10, 25, 50, 100]
    
    print("\n" + "="*80)
    print("STRESS TEST RESULTS")
    print("="*80)
    print(f"{'Batch Size':<10} {'Pillow Seq':<12} {'Pillow Thread':<15} {'Rust Parallel':<15} {'Best Method'}")
    print("-" * 80)
    
    for batch_size in batch_sizes:
        if batch_size > len(large_paths):
            continue
            
        test_paths = large_paths[:batch_size]
        
        # Test each method
        pillow_seq_results, pillow_seq_time = pillow_sequential(test_paths)
        pillow_thread_results, pillow_thread_time = pillow_threaded(test_paths, max_workers=6)
        rust_results, rust_time = rust_parallel(test_paths)
        
        # Find the fastest
        times = {
            'Pillow Seq': pillow_seq_time,
            'Pillow Thread': pillow_thread_time, 
            'Rust Parallel': rust_time
        }
        fastest = min(times.keys(), key=lambda k: times[k])
        
        print(f"{batch_size:<10} {pillow_seq_time:<12.4f} {pillow_thread_time:<15.4f} {rust_time:<15.4f} {fastest}")
        
        # Show speedups
        if batch_size >= 50:  # Only show detailed analysis for larger batches
            print(f"           Speedup vs Sequential: Rust={pillow_seq_time/rust_time:.2f}x, Thread={pillow_seq_time/pillow_thread_time:.2f}x")
            print(f"           Images/second: Rust={batch_size/rust_time:.1f}, Pillow={batch_size/pillow_seq_time:.1f}, Thread={batch_size/pillow_thread_time:.1f}")
    
    print("\n" + "="*50)
    print("THROUGHPUT ANALYSIS")
    print("="*50)
    
    # Test maximum throughput with 100 images
    if len(large_paths) >= 100:
        test_paths = large_paths[:100]
        
        print(f"Testing maximum throughput with {len(test_paths)} images...")
        
        # Multiple runs for accuracy
        rust_times = []
        pillow_thread_times = []
        
        for _ in range(3):
            _, rust_time = rust_parallel(test_paths)
            rust_times.append(rust_time)
            
            _, pillow_time = pillow_threaded(test_paths, max_workers=8) 
            pillow_thread_times.append(pillow_time)
        
        best_rust = min(rust_times)
        best_pillow_thread = min(pillow_thread_times)
        
        print(f"\nBest performance (3 runs):")
        print(f"Rust Parallel:     {best_rust:.4f}s ({100/best_rust:.1f} images/sec)")
        print(f"Pillow Threaded:   {best_pillow_thread:.4f}s ({100/best_pillow_thread:.1f} images/sec)")
        print(f"Speedup: {best_pillow_thread/best_rust:.2f}x")
        
        # Calculate pixels per second
        total_pixels = sum(img[1] * img[2] for img in rust_results)
        rust_pixels_per_sec = total_pixels / best_rust
        pillow_pixels_per_sec = total_pixels / best_pillow_thread
        
        print(f"\nPixel processing speed:")
        print(f"Rust:   {rust_pixels_per_sec/1_000_000:.1f} million pixels/sec")
        print(f"Pillow: {pillow_pixels_per_sec/1_000_000:.1f} million pixels/sec")

if __name__ == "__main__":
    stress_test()
    
    # Cleanup
    print("\nCleaning up test files...")
    import shutil
    if os.path.exists("large_test"):
        shutil.rmtree("large_test")
    print("Done!")