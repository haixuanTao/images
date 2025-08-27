//! Fast parallel image reading library with Python bindings.
//!
//! This library provides high-performance image reading capabilities using Rust's
//! image processing libraries with Python bindings. It leverages parallel processing
//! for optimal performance when reading multiple images.
//!
//! # Features
//! - Parallel image processing using Rayon
//! - Support for multiple formats: PNG, JPEG, AVIF, WebP, GIF, TIFF, BMP
//! - Fast format detection based on file extensions
//! - Automatic RGB conversion
//! - Graceful error handling (returns None for failed reads)
//!
//! # Example
//! ```python
//! import images_rs
//! import numpy as np
//!
//! # Read multiple images in parallel
//! images = images_rs.read(['photo1.jpg', 'photo2.png', 'photo3.avif'])
//! 
//! # Process successfully loaded images
//! for i, img in enumerate(images):
//!     if img is not None:
//!         print(f"Image {i}: shape {img.shape}, dtype {img.dtype}")
//! ```

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use numpy::{PyArray1, PyArray3};
use numpy::ndarray::Array3;
use rayon::prelude::*;
use image::{ImageReader, ImageError, ImageFormat};
use std::path::Path;

/// Internal error type for image reading operations.
/// 
/// This enum wraps different types of errors that can occur during
/// image reading and provides a unified error handling interface.
#[derive(Debug)]
enum ReadError {
    /// Error from the image processing library
    ImageError(ImageError),
    /// I/O error when accessing files
    IoError(std::io::Error),
}

impl From<ImageError> for ReadError {
    fn from(err: ImageError) -> Self {
        ReadError::ImageError(err)
    }
}

impl From<std::io::Error> for ReadError {
    fn from(err: std::io::Error) -> Self {
        ReadError::IoError(err)
    }
}

/// Fast image format detection based on file extension.
///
/// This function provides rapid format detection by examining the file extension,
/// which is much faster than content-based detection. It supports all major
/// image formats commonly used in applications.
///
/// # Arguments
/// * `path` - The file path to examine
///
/// # Returns
/// * `Some(ImageFormat)` if the extension is recognized
/// * `None` if the extension is unknown or missing
///
/// # Supported Formats
/// - AVIF (.avif)
/// - JPEG (.jpg, .jpeg) 
/// - PNG (.png)
/// - WebP (.webp)
/// - GIF (.gif)
/// - TIFF (.tiff, .tif)
/// - BMP (.bmp)
fn guess_format_from_extension(path: &str) -> Option<ImageFormat> {
    let path = Path::new(path);
    match path.extension()?.to_str()?.to_lowercase().as_str() {
        "avif" => Some(ImageFormat::Avif),
        "jpg" | "jpeg" => Some(ImageFormat::Jpeg),
        "png" => Some(ImageFormat::Png),
        "webp" => Some(ImageFormat::WebP),
        "gif" => Some(ImageFormat::Gif),
        "tiff" | "tif" => Some(ImageFormat::Tiff),
        "bmp" => Some(ImageFormat::Bmp),
        _ => None,
    }
}

/// Read multiple images in parallel and return them as numpy arrays.
///
/// This is the main entry point for the Python extension. It efficiently reads
/// multiple image files concurrently using Rust's high-performance image processing
/// libraries and returns them as a list of numpy arrays.
///
/// # Arguments
/// * `py` - Python interpreter state
/// * `paths` - Python list of file paths (strings or Path-like objects)
/// * `num_threads` - Optional number of threads for parallel processing
///
/// # Returns
/// * `PyResult<PyObject>` - Python list containing numpy arrays or None for failed reads
///
/// # Features
/// - Automatic RGB conversion regardless of input format
/// - Fast format detection using file extensions with fallback to content detection
/// - Parallel processing using Rayon for optimal performance
/// - Graceful error handling - failed reads return None instead of crashing
/// - Direct memory management for efficient numpy array creation
///
/// # Thread Pool Behavior
/// The global thread pool can only be initialized once per process. If `num_threads`
/// is specified on subsequent calls, it will be silently ignored to prevent panics.
#[pyfunction]
#[pyo3(signature = (paths, num_threads = None))]
fn read(py: Python, paths: &Bound<'_, PyList>, num_threads: Option<usize>) -> PyResult<PyObject> {
    // Set the number of threads if specified
    // Note: Rayon's global thread pool can only be initialized once per process
    if let Some(threads) = num_threads {
        if let Err(_) = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build_global() 
        {
            // Thread pool already initialized, ignore silently
            // This is expected in testing or multiple function calls
        }
    }
    // Extract paths once - handle both strings and Path objects
    let path_strings: Vec<String> = paths
        .iter()
        .map(|item| {
            // Try to extract as string first
            if let Ok(s) = item.extract::<String>() {
                Ok(s)
            } else {
                // Try to get string representation of Path objects
                item.str()?.extract::<String>()
            }
        })
        .collect::<Result<Vec<_>, _>>()?;

    // Pre-allocate results
    let mut results = Vec::with_capacity(path_strings.len());
    
    // Parallel processing with optimizations
    path_strings
        .par_iter()
        .map(|path| -> Result<(Vec<u8>, u32, u32), ReadError> {
            // Try format from extension first (much faster)
            let mut reader = ImageReader::open(path)?;
            
            if reader.format().is_none() {
                if let Some(format) = guess_format_from_extension(path) {
                    reader.set_format(format);
                } else {
                    // Only do expensive format guessing if extension fails
                    reader = reader.with_guessed_format()?;
                }
            }
            
            // Decode and convert in one go
            let img = reader.decode()?;
            let rgb_img = img.to_rgb8();
            let (width, height) = rgb_img.dimensions();
            
            // Direct access to raw data (no copying)
            let data = rgb_img.into_raw();
            
            Ok((data, width, height))
        })
        .collect_into_vec(&mut results);

    // Process results into Python objects
    let mut images = Vec::with_capacity(results.len());

    for (i, result) in results.into_iter().enumerate() {
        match result {
            Ok((data, width, height)) => {
                // Create numpy array directly from raw data with proper shape
                let array = Array3::from_shape_vec(
                    (height as usize, width as usize, 3),
                    data
                ).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Array shape error: {}", e)))?;
                
                let py_array = PyArray3::from_owned_array_bound(py, array);
                images.push(py_array.to_object(py));
            }
            Err(e) => {
                // Log error and push None placeholder
                eprintln!("Error reading image at index {}: {:?}", i, e);
                images.push(py.None());
            }
        }
    }

    // Return list of numpy arrays (with None for failed images)
    let py_list = PyList::new_bound(py, images);
    Ok(py_list.to_object(py))
}


/// Python module definition for images_rs.
///
/// This module exports the `read` function as the primary interface for
/// parallel image reading functionality. The module is compiled as a
/// Python extension using PyO3 and maturin.
///
/// # Exported Functions
/// - `read(paths, num_threads=None)` - Read multiple images in parallel
#[pymodule]
fn images_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read, m)?)?;
    Ok(())
}