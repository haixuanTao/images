use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use numpy::{PyArray1, PyArray3};
use numpy::ndarray::Array3;
use rayon::prelude::*;
use image::{ImageReader, ImageError, ImageFormat};
use std::path::Path;

#[derive(Debug)]
enum ReadError {
    ImageError(ImageError),
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

// Fast format detection by file extension
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

#[pyfunction]
fn read_images_parallel(py: Python, paths: &Bound<'_, PyList>) -> PyResult<PyObject> {
    // Extract paths once
    let path_strings: Vec<String> = paths
        .iter()
        .map(|item| item.extract::<String>())
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
    let mut errors = Vec::new();

    for (i, result) in results.into_iter().enumerate() {
        match result {
            Ok((data, width, height)) => {
                // Create numpy array directly from raw data with proper shape
                let array = Array3::from_shape_vec(
                    (height as usize, width as usize, 3),
                    data
                ).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Array shape error: {}", e)))?;
                
                let py_array = PyArray3::from_owned_array_bound(py, array);

                images.push((py_array.to_object(py), width, height));
            }
            Err(e) => {
                errors.push((i, format!("{:?}", e)));
            }
        }
    }

    let result_dict = PyDict::new_bound(py);
    result_dict.set_item("images", images)?;
    result_dict.set_item("errors", errors)?;

    Ok(result_dict.to_object(py))
}

#[pyfunction]
fn read_images_as_bytes_parallel(py: Python, paths: &Bound<'_, PyList>) -> PyResult<PyObject> {
    // Extract paths once
    let path_strings: Vec<String> = paths
        .iter()
        .map(|item| item.extract::<String>())
        .collect::<Result<Vec<_>, _>>()?;

    // Pre-allocate results  
    let mut results = Vec::with_capacity(path_strings.len());

    // Parallel processing
    path_strings
        .par_iter()
        .map(|path| -> Result<(Vec<u8>, u32, u32), ReadError> {
            let mut reader = ImageReader::open(path)?;
            
            if reader.format().is_none() {
                if let Some(format) = guess_format_from_extension(path) {
                    reader.set_format(format);
                } else {
                    reader = reader.with_guessed_format()?;
                }
            }

            let img = reader.decode()?;
            let rgb_img = img.to_rgb8();
            let (width, height) = rgb_img.dimensions();
            
            let data = rgb_img.into_raw();
            Ok((data, width, height))
        })
        .collect_into_vec(&mut results);

    // Process results
    let mut images = Vec::with_capacity(results.len());
    let mut errors = Vec::new();

    for (i, result) in results.into_iter().enumerate() {
        match result {
            Ok((data, width, height)) => {
                // Direct 1D array creation - no reshaping overhead
                let py_array = PyArray1::from_vec_bound(py, data);
                images.push((py_array.to_object(py), width, height));
            }
            Err(e) => {
                errors.push((i, format!("{:?}", e)));
            }
        }
    }

    let result_dict = PyDict::new_bound(py);
    result_dict.set_item("images", images)?;
    result_dict.set_item("errors", errors)?;

    Ok(result_dict.to_object(py))
}

#[pymodule]
fn images_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_images_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(read_images_as_bytes_parallel, m)?)?;
    Ok(())
}