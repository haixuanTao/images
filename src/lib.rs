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
#[pyo3(signature = (paths, num_threads = None))]
fn read(py: Python, paths: &Bound<'_, PyList>, num_threads: Option<usize>) -> PyResult<PyObject> {
    // Set the number of threads if specified
    if let Some(threads) = num_threads {
        rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build_global()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to set thread count: {}", e)))?;
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


#[pymodule]
fn images(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read, m)?)?;
    Ok(())
}