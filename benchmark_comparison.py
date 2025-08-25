#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image
import parallel_read_avif
import glob
import concurrent.futures
import threading
from pathlib import Path

def pillow_read_single(path):
    """Read a single image using Pillow"""
    try:
        with Image.open(path) as img:
            rgb_img = img.convert('RGB')
            return np.array(rgb_img), rgb_img.size[0], rgb_img.size[1]
    except Exception as e:
        return None, str(e)

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
    results = []
    errors = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {executor.submit(pillow_read_single, path): i 
                          for i, path in enumerate(paths)}
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                if result[0] is not None:
                    results.append((index, result[0], result[1], result[2]))
                else:
                    errors.append((index, result[1]))
            except Exception as e:
                errors.append((index, str(e)))
    
    # Sort results by original index
    results.sort(key=lambda x: x[0])
    final_results = [(r[1], r[2], r[3]) for r in results]
    
    return {"images": final_results, "errors": errors}

def benchmark_implementations():
    """Benchmark different implementations"""
    
    # Get AVIF test images
    avif_paths = sorted(glob.glob("images/test_avif_*.avif"))
    all_paths = sorted(glob.glob("images/test_*.png") + 
                      glob.glob("images/test_*.jpg") + 
                      glob.glob("images/test_*.avif"))
    
    print("=== AVIF Performance Comparison ===")
    print(f"Testing with {len(avif_paths)} AVIF images")
    print(f"AVIF images: {[Path(p).name for p in avif_paths[:3]]}...")
    print()
    
    # Test 1: AVIF only - Sequential Pillow
    print("1. Pillow Sequential (AVIF only):")
    start_time = time.time()
    pillow_seq_result = pillow_read_sequential(avif_paths)
    pillow_seq_time = time.time() - start_time
    
    print(f"   Time: {pillow_seq_time:.4f}s")
    print(f"   Success: {len(pillow_seq_result['images'])}/{len(avif_paths)}")
    print(f"   Errors: {len(pillow_seq_result['errors'])}")
    if pillow_seq_result['errors']:
        for i, err in pillow_seq_result['errors'][:3]:
            print(f"      {avif_paths[i]}: {err}")
    print()
    
    # Test 2: AVIF only - Threaded Pillow
    print("2. Pillow ThreadPool (AVIF only):")
    start_time = time.time()
    pillow_thread_result = pillow_read_threaded(avif_paths)
    pillow_thread_time = time.time() - start_time
    
    print(f"   Time: {pillow_thread_time:.4f}s")
    print(f"   Success: {len(pillow_thread_result['images'])}/{len(avif_paths)}")
    print(f"   Errors: {len(pillow_thread_result['errors'])}")
    print()
    
    # Test 3: AVIF only - Our Rust implementation
    print("3. Rust Parallel (AVIF only):")
    start_time = time.time()
    rust_result = parallel_read_avif.read_images_parallel(avif_paths)
    rust_time = time.time() - start_time
    
    print(f"   Time: {rust_time:.4f}s")
    print(f"   Success: {len(rust_result['images'])}/{len(avif_paths)}")
    print(f"   Errors: {len(rust_result['errors'])}")
    print()
    
    # Calculate speedups for AVIF
    if pillow_seq_time > 0 and rust_time > 0:
        speedup_vs_seq = pillow_seq_time / rust_time
        print(f"   🚀 Rust vs Pillow Sequential: {speedup_vs_seq:.2f}x faster")
    
    if pillow_thread_time > 0 and rust_time > 0:
        speedup_vs_thread = pillow_thread_time / rust_time
        print(f"   🚀 Rust vs Pillow Threaded: {speedup_vs_thread:.2f}x faster")
    print()
    
    print("=== Mixed Format Performance Comparison ===")
    print(f"Testing with {len(all_paths)} mixed format images")
    format_counts = {}
    for path in all_paths:
        ext = Path(path).suffix.lower()
        format_counts[ext] = format_counts.get(ext, 0) + 1
    print(f"Formats: {dict(format_counts)}")
    print()
    
    # Test 4: Mixed formats - Sequential Pillow
    print("4. Pillow Sequential (All formats):")
    start_time = time.time()
    pillow_mixed_seq = pillow_read_sequential(all_paths)
    pillow_mixed_seq_time = time.time() - start_time
    
    print(f"   Time: {pillow_mixed_seq_time:.4f}s")
    print(f"   Success: {len(pillow_mixed_seq['images'])}/{len(all_paths)}")
    print(f"   Avg per image: {pillow_mixed_seq_time/len(all_paths):.4f}s")
    print()
    
    # Test 5: Mixed formats - Threaded Pillow
    print("5. Pillow ThreadPool (All formats):")
    start_time = time.time()
    pillow_mixed_thread = pillow_read_threaded(all_paths)
    pillow_mixed_thread_time = time.time() - start_time
    
    print(f"   Time: {pillow_mixed_thread_time:.4f}s")
    print(f"   Success: {len(pillow_mixed_thread['images'])}/{len(all_paths)}")
    print(f"   Avg per image: {pillow_mixed_thread_time/len(all_paths):.4f}s")
    print()
    
    # Test 6: Mixed formats - Our Rust implementation
    print("6. Rust Parallel (All formats):")
    start_time = time.time()
    rust_mixed_result = parallel_read_avif.read_images_parallel(all_paths)
    rust_mixed_time = time.time() - start_time
    
    print(f"   Time: {rust_mixed_time:.4f}s")
    print(f"   Success: {len(rust_mixed_result['images'])}/{len(all_paths)}")
    print(f"   Avg per image: {rust_mixed_time/len(all_paths):.4f}s")
    print()
    
    # Calculate speedups for mixed formats
    if pillow_mixed_seq_time > 0 and rust_mixed_time > 0:
        speedup_mixed_seq = pillow_mixed_seq_time / rust_mixed_time
        print(f"   🚀 Rust vs Pillow Sequential: {speedup_mixed_seq:.2f}x faster")
    
    if pillow_mixed_thread_time > 0 and rust_mixed_time > 0:
        speedup_mixed_thread = pillow_mixed_thread_time / rust_mixed_time
        print(f"   🚀 Rust vs Pillow Threaded: {speedup_mixed_thread:.2f}x faster")
    print()
    
    # Memory usage comparison
    print("=== Memory Usage Comparison ===")
    if rust_result['images'] and pillow_seq_result['images']:
        rust_array = rust_result['images'][0][0]
        pillow_array = pillow_seq_result['images'][0][0] if pillow_seq_result['images'] else None
        
        if pillow_array is not None:
            print(f"Rust array dtype: {rust_array.dtype}")
            print(f"Pillow array dtype: {pillow_array.dtype}")
            print(f"Same data shape: {rust_array.shape == pillow_array.shape}")
            
            # Check if data is similar (allowing for minor differences due to decoding)
            if rust_array.shape == pillow_array.shape:
                diff = np.abs(rust_array.astype(int) - pillow_array.astype(int))
                max_diff = np.max(diff)
                mean_diff = np.mean(diff)
                print(f"Max pixel difference: {max_diff}")
                print(f"Mean pixel difference: {mean_diff:.2f}")
                
                if max_diff <= 2:  # Allow for minor rounding differences
                    print("✅ Decoded data is essentially identical")
                else:
                    print("⚠️  Significant differences in decoded data")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    results_summary = [
        ("AVIF Sequential (Pillow)", pillow_seq_time, len(pillow_seq_result['images'])),
        ("AVIF Threaded (Pillow)", pillow_thread_time, len(pillow_thread_result['images'])),
        ("AVIF Parallel (Rust)", rust_time, len(rust_result['images'])),
        ("Mixed Sequential (Pillow)", pillow_mixed_seq_time, len(pillow_mixed_seq['images'])),
        ("Mixed Threaded (Pillow)", pillow_mixed_thread_time, len(pillow_mixed_thread['images'])),
        ("Mixed Parallel (Rust)", rust_mixed_time, len(rust_mixed_result['images'])),
    ]
    
    for name, timing, success_count in results_summary:
        print(f"{name:.<30} {timing:.4f}s ({success_count} images)")

if __name__ == "__main__":
    benchmark_implementations()