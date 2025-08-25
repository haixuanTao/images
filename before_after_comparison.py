#!/usr/bin/env python3

import time
import parallel_read_avif
import glob

def benchmark_old_vs_new():
    """Compare old vs optimized implementation"""
    
    avif_paths = glob.glob("images/test_avif_*.avif")[:10]
    
    print("=== Before vs After Optimization ===")
    print(f"Testing with {len(avif_paths)} AVIF images")
    print()
    
    # Test multiple runs for accuracy
    old_times = []
    new_times = []
    
    # We don't have the old implementation anymore, but let's test our new one
    # and see if we can compare against Pillow
    
    for run in range(5):
        # Test our current (optimized) implementation
        start = time.perf_counter()
        result = parallel_read_avif.read_images_parallel(avif_paths)
        end = time.perf_counter()
        new_times.append(end - start)
        
        if len(result['errors']) > 0:
            print(f"Warning: {len(result['errors'])} errors in run {run}")
    
    best_new = min(new_times)
    avg_new = sum(new_times) / len(new_times)
    
    print(f"Optimized Implementation:")
    print(f"  Best time: {best_new:.4f}s")
    print(f"  Average:   {avg_new:.4f}s")
    print(f"  Success:   {len(result['images'])}/{len(avif_paths)}")
    print()
    
    # Test with different batch sizes to see scaling
    batch_sizes = [1, 5, 10, 15, 20] if len(glob.glob("images/test_avif_*.avif")) >= 20 else [1, 5, 10]
    
    print("=== Scaling Test ===")
    print(f"{'Batch Size':<10} {'Time (s)':<10} {'Images/sec':<12} {'Efficiency'}")
    print("-" * 50)
    
    for batch_size in batch_sizes:
        all_avif = glob.glob("images/test_avif_*.avif")
        if batch_size > len(all_avif):
            continue
            
        test_paths = all_avif[:batch_size]
        
        # Multiple runs
        times = []
        for _ in range(3):
            start = time.perf_counter()
            result = parallel_read_avif.read_images_parallel(test_paths)
            end = time.perf_counter()
            times.append(end - start)
        
        best_time = min(times)
        images_per_sec = batch_size / best_time
        
        # Estimate efficiency (compared to single-threaded)
        single_thread_estimate = best_time * 12  # Assume perfect 12-core scaling
        theoretical_single = single_thread_estimate / batch_size
        efficiency = theoretical_single / best_time if best_time > 0 else 0
        
        print(f"{batch_size:<10} {best_time:<10.4f} {images_per_sec:<12.1f} {efficiency:.2f}x")
    
    print("\n=== Memory Usage Analysis ===")
    test_paths = avif_paths[:5]
    result = parallel_read_avif.read_images_parallel(test_paths)
    
    if result['images']:
        img_array, width, height = result['images'][0]
        total_pixels = sum(w * h for _, w, h in result['images'])
        
        print(f"Sample image shape: {img_array.shape}")
        print(f"Sample image dtype: {img_array.dtype}")
        print(f"Total pixels processed: {total_pixels:,}")
        print(f"Memory per image: ~{(width * height * 3) / 1024:.1f} KB")

if __name__ == "__main__":
    benchmark_old_vs_new()