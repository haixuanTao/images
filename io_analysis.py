#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image
import parallel_read_avif
import glob
import os
import threading
from concurrent.futures import ThreadPoolExecutor

def analyze_io_vs_cpu():
    """Analyze I/O vs CPU time breakdown"""
    
    avif_paths = glob.glob("images/test_avif_*.avif")[:10]
    
    print("=== I/O vs CPU Analysis ===")
    print(f"Testing with {len(avif_paths)} AVIF images")
    
    # Test 1: Pure file reading (no decoding)
    print("\n1. Pure File I/O (no decoding):")
    
    start = time.perf_counter()
    file_sizes = []
    for path in avif_paths:
        with open(path, 'rb') as f:
            data = f.read()
            file_sizes.append(len(data))
    io_time = time.perf_counter() - start
    
    total_bytes = sum(file_sizes)
    print(f"   Sequential I/O: {io_time:.4f}s")
    print(f"   Total bytes: {total_bytes:,} ({total_bytes/1024/1024:.1f} MB)")
    print(f"   I/O speed: {total_bytes/io_time/1024/1024:.1f} MB/s")
    
    # Test parallel I/O
    def read_file(path):
        with open(path, 'rb') as f:
            return len(f.read())
    
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(read_file, avif_paths))
    parallel_io_time = time.perf_counter() - start
    
    print(f"   Parallel I/O: {parallel_io_time:.4f}s")
    print(f"   I/O speedup: {io_time/parallel_io_time:.2f}x")
    
    # Test 2: Pillow decode time breakdown
    print("\n2. Pillow Decode Analysis:")
    
    # Pre-load into memory
    file_data = {}
    for path in avif_paths:
        with open(path, 'rb') as f:
            file_data[path] = f.read()
    
    # Test decode from memory vs file
    start = time.perf_counter()
    pillow_from_file = []
    for path in avif_paths:
        with Image.open(path) as img:
            rgb = img.convert('RGB')
            pillow_from_file.append(np.array(rgb))
    pillow_file_time = time.perf_counter() - start
    
    # From memory
    import io
    start = time.perf_counter()
    pillow_from_memory = []
    for path in avif_paths:
        with Image.open(io.BytesIO(file_data[path])) as img:
            rgb = img.convert('RGB')
            pillow_from_memory.append(np.array(rgb))
    pillow_memory_time = time.perf_counter() - start
    
    print(f"   Pillow from file: {pillow_file_time:.4f}s")
    print(f"   Pillow from memory: {pillow_memory_time:.4f}s")
    print(f"   I/O overhead: {((pillow_file_time - pillow_memory_time)/pillow_file_time)*100:.1f}%")
    
    # Test 3: Our Rust implementation analysis
    print("\n3. Rust Implementation Analysis:")
    
    # Test our implementation
    start = time.perf_counter()
    rust_result = parallel_read_avif.read_images_parallel(avif_paths)
    rust_time = time.perf_counter() - start
    
    print(f"   Rust parallel: {rust_time:.4f}s")
    print(f"   Success: {len(rust_result['images'])}")
    
    # Compare against theoretical maximum
    pure_decode_time = pillow_memory_time  # CPU-only time
    theoretical_parallel_time = pure_decode_time / 12  # 12 cores
    theoretical_with_io = parallel_io_time + theoretical_parallel_time
    
    print(f"\n4. Theoretical Analysis:")
    print(f"   Pure CPU decode time: {pure_decode_time:.4f}s")
    print(f"   Theoretical 12-core parallel: {theoretical_parallel_time:.4f}s")
    print(f"   Theoretical + parallel I/O: {theoretical_with_io:.4f}s")
    print(f"   Actual Rust time: {rust_time:.4f}s")
    print(f"   Efficiency: {theoretical_with_io/rust_time:.2f} (1.0 = perfect)")
    
    # Calculate what's limiting us
    io_fraction = parallel_io_time / rust_time
    cpu_fraction = 1 - io_fraction
    
    print(f"\n5. Bottleneck Analysis:")
    print(f"   I/O accounts for ~{io_fraction*100:.1f}% of total time")
    print(f"   CPU accounts for ~{cpu_fraction*100:.1f}% of total time")
    
    if io_fraction > 0.3:
        print("   🚨 I/O BOUND - File reading is limiting parallelism")
    elif cpu_fraction > 0.7:
        print("   🔥 CPU BOUND - Decoding is the main bottleneck")
    else:
        print("   ⚖️  MIXED - Both I/O and CPU contribute to bottleneck")

def test_different_storage():
    """Test if storage type affects performance"""
    
    avif_paths = glob.glob("images/test_avif_*.avif")[:5]
    
    print("\n=== Storage Impact Test ===")
    
    # Test 1: Normal files
    start = time.perf_counter()
    rust_result = parallel_read_avif.read_images_parallel(avif_paths)
    normal_time = time.perf_counter() - start
    print(f"Normal files: {normal_time:.4f}s")
    
    # Test 2: Copy to /tmp (different filesystem, possibly RAM-backed)
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_paths = []
        for path in avif_paths:
            tmp_path = os.path.join(tmpdir, os.path.basename(path))
            shutil.copy2(path, tmp_path)
            tmp_paths.append(tmp_path)
        
        start = time.perf_counter()
        tmp_result = parallel_read_avif.read_images_parallel(tmp_paths)
        tmp_time = time.perf_counter() - start
        
        print(f"Temp files: {tmp_time:.4f}s")
        print(f"Storage speedup: {normal_time/tmp_time:.2f}x")

if __name__ == "__main__":
    analyze_io_vs_cpu()
    test_different_storage()