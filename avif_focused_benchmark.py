#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image
import parallel_read_avif
import concurrent.futures
import glob
import shutil
import os

def create_avif_only_dataset():
    """Create a dataset with ONLY AVIF images of various sizes"""
    
    # Create different sized AVIF images
    os.makedirs("avif_test", exist_ok=True)
    
    # Clean existing
    for f in glob.glob("avif_test/*.avif"):
        os.remove(f)
    
    avif_paths = []
    
    print("Creating AVIF-only test dataset...")
    
    # Create AVIF images of different sizes and complexities
    sizes_and_types = [
        (100, 100, "gradient"),
        (200, 150, "noise"),
        (300, 200, "solid"),
        (400, 300, "checkerboard"),
        (150, 100, "radial"),
        (250, 180, "stripes"),
        (180, 120, "circles"),
        (320, 240, "complex")
    ]
    
    for i, (width, height, pattern_type) in enumerate(sizes_and_types):
        # Create different patterns
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        
        if pattern_type == "gradient":
            for y in range(height):
                for x in range(width):
                    arr[y, x, 0] = (x * 255) // width
                    arr[y, x, 1] = (y * 255) // height
                    arr[y, x, 2] = 128
                    
        elif pattern_type == "noise":
            arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            
        elif pattern_type == "solid":
            color = [(i * 30) % 256, (i * 50) % 256, (i * 70) % 256]
            arr[:] = color
            
        elif pattern_type == "checkerboard":
            for y in range(height):
                for x in range(width):
                    if (x // 20 + y // 20) % 2:
                        arr[y, x] = [255, 255, 255]
                    else:
                        arr[y, x] = [0, 0, 0]
                        
        elif pattern_type == "radial":
            center_x, center_y = width // 2, height // 2
            for y in range(height):
                for x in range(width):
                    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    max_dist = np.sqrt(center_x**2 + center_y**2)
                    intensity = int(255 * (dist / max_dist)) if max_dist > 0 else 0
                    arr[y, x] = [intensity, 255 - intensity, 128]
                    
        elif pattern_type == "stripes":
            for y in range(height):
                if (y // 10) % 2:
                    arr[y, :] = [255, 100, 50]
                else:
                    arr[y, :] = [50, 100, 255]
                    
        elif pattern_type == "circles":
            for y in range(height):
                for x in range(width):
                    dist_from_center = np.sqrt((x - width//2)**2 + (y - height//2)**2)
                    if int(dist_from_center) % 30 < 15:
                        arr[y, x] = [255, 200, 100]
                    else:
                        arr[y, x] = [100, 200, 255]
                        
        else:  # complex
            # Combination pattern
            for y in range(height):
                for x in range(width):
                    r = int(128 + 127 * np.sin(x / 20))
                    g = int(128 + 127 * np.sin(y / 30))
                    b = int(128 + 127 * np.sin((x + y) / 25))
                    arr[y, x] = [r, g, b]
        
        # Save as AVIF
        img = Image.fromarray(arr)
        path = f"avif_test/test_avif_{i:02d}_{width}x{height}_{pattern_type}.avif"
        img.save(path, "AVIF", quality=75)
        avif_paths.append(path)
        print(f"  Created: {path}")
    
    # Duplicate some for larger batches
    base_paths = avif_paths.copy()
    for i in range(len(base_paths) * 4):  # Create 40 total (8 * 5)
        source = base_paths[i % len(base_paths)]
        dest = f"avif_test/dup_{i:03d}.avif"
        shutil.copy2(source, dest)
        avif_paths.append(dest)
    
    print(f"Created {len(avif_paths)} AVIF images for testing")
    return avif_paths

def pillow_avif_sequential(paths):
    """Pillow AVIF reading - sequential"""
    results = []
    errors = []
    start = time.perf_counter()
    
    for i, path in enumerate(paths):
        try:
            with Image.open(path) as img:
                # Verify it's actually AVIF
                if img.format != 'AVIF':
                    errors.append((i, f"Not AVIF format: {img.format}"))
                    continue
                    
                rgb_img = img.convert('RGB')
                array = np.array(rgb_img)
                results.append((array, rgb_img.size[0], rgb_img.size[1]))
        except Exception as e:
            errors.append((i, str(e)))
    
    end = time.perf_counter()
    return results, errors, end - start

def pillow_avif_threaded(paths, max_workers=4):
    """Pillow AVIF reading - threaded"""
    def read_single(args):
        i, path = args
        try:
            with Image.open(path) as img:
                if img.format != 'AVIF':
                    raise Exception(f"Not AVIF format: {img.format}")
                    
                rgb_img = img.convert('RGB')
                return i, np.array(rgb_img), rgb_img.size[0], rgb_img.size[1]
        except Exception as e:
            raise Exception(f"Index {i}: {str(e)}")
    
    results = []
    errors = []
    start = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        indexed_paths = [(i, path) for i, path in enumerate(paths)]
        future_to_args = {executor.submit(read_single, args): args for args in indexed_paths}
        
        for future in concurrent.futures.as_completed(future_to_args):
            args = future_to_args[future]
            try:
                i, array, width, height = future.result()
                results.append((i, array, width, height))
            except Exception as e:
                errors.append((args[0], str(e)))
    
    # Sort by index
    results.sort(key=lambda x: x[0])
    final_results = [(r[1], r[2], r[3]) for r in results]
    
    end = time.perf_counter()
    return final_results, errors, end - start

def rust_avif_parallel(paths):
    """Our Rust AVIF implementation"""
    start = time.perf_counter()
    result = parallel_read_avif.read_images_parallel(paths)
    end = time.perf_counter()
    
    return result['images'], result['errors'], end - start

def avif_focused_benchmark():
    """Run AVIF-focused benchmark"""
    
    print("="*70)
    print("AVIF-SPECIFIC PERFORMANCE COMPARISON")
    print("="*70)
    
    avif_paths = create_avif_only_dataset()
    
    # Test different batch sizes - AVIF only
    batch_sizes = [1, 5, 10, 20, 40]
    
    print(f"\n{'Batch':<6} {'Pillow Seq':<12} {'Pillow Thread':<15} {'Rust dav1d':<12} {'Best':<15} {'Rust Speedup':<12}")
    print("-" * 80)
    
    for batch_size in batch_sizes:
        if batch_size > len(avif_paths):
            continue
            
        test_paths = avif_paths[:batch_size]
        
        # Run each test 3 times and take the best
        pillow_seq_times = []
        pillow_thread_times = []
        rust_times = []
        
        for run in range(3):
            # Pillow Sequential
            results, errors, time_taken = pillow_avif_sequential(test_paths)
            if len(errors) == 0:  # Only count if successful
                pillow_seq_times.append(time_taken)
            
            # Pillow Threaded  
            results, errors, time_taken = pillow_avif_threaded(test_paths, max_workers=6)
            if len(errors) == 0:
                pillow_thread_times.append(time_taken)
            
            # Rust Parallel
            results, errors, time_taken = rust_avif_parallel(test_paths)
            if len(errors) == 0:
                rust_times.append(time_taken)
        
        if pillow_seq_times and pillow_thread_times and rust_times:
            best_pillow_seq = min(pillow_seq_times)
            best_pillow_thread = min(pillow_thread_times)
            best_rust = min(rust_times)
            
            # Find best overall
            times = {
                'Pillow Seq': best_pillow_seq,
                'Pillow Thread': best_pillow_thread,
                'Rust dav1d': best_rust
            }
            best_method = min(times.keys(), key=lambda k: times[k])
            
            # Calculate speedups
            seq_speedup = best_pillow_seq / best_rust
            thread_speedup = best_pillow_thread / best_rust
            
            print(f"{batch_size:<6} {best_pillow_seq:<12.4f} {best_pillow_thread:<15.4f} {best_rust:<12.4f} {best_method:<15} {seq_speedup:.2f}x vs seq")
            
            # Show detailed analysis for larger batches
            if batch_size >= 20:
                images_per_sec_rust = batch_size / best_rust
                images_per_sec_pillow = batch_size / best_pillow_seq
                print(f"       AVIF/sec: Rust={images_per_sec_rust:.0f}, Pillow={images_per_sec_pillow:.0f}")
        else:
            print(f"{batch_size:<6} Error in one or more tests")
    
    print("\n" + "="*50)
    print("AVIF DECODING ANALYSIS")
    print("="*50)
    
    # Analyze what makes AVIF special
    if len(avif_paths) >= 10:
        test_paths = avif_paths[:10]
        
        print(f"Analyzing AVIF decoding with {len(test_paths)} diverse images...")
        
        # Get detailed info about the images
        rust_results, rust_errors, rust_time = rust_avif_parallel(test_paths)
        pillow_results, pillow_errors, pillow_time = pillow_avif_sequential(test_paths)
        
        if rust_results and pillow_results:
            print(f"\nRust (dav1d decoder):   {rust_time:.4f}s")
            print(f"Pillow (AVIF support): {pillow_time:.4f}s") 
            print(f"Rust advantage: {pillow_time/rust_time:.2f}x faster")
            
            # Calculate total pixels processed
            total_pixels = sum(img[1] * img[2] for img in rust_results)
            rust_mpps = (total_pixels / rust_time) / 1_000_000  # Megapixels per second
            pillow_mpps = (total_pixels / pillow_time) / 1_000_000
            
            print(f"\nPixel throughput:")
            print(f"Rust:   {rust_mpps:.1f} megapixels/sec")
            print(f"Pillow: {pillow_mpps:.1f} megapixels/sec")
            print(f"Advantage: {rust_mpps/pillow_mpps:.2f}x faster pixel processing")

if __name__ == "__main__":
    try:
        avif_focused_benchmark()
    finally:
        # Cleanup
        print("\nCleaning up...")
        if os.path.exists("avif_test"):
            shutil.rmtree("avif_test")
        print("Done!")