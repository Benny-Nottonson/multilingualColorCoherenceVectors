use reqwest::blocking::get;
use std::io::{Read, Cursor};
use image::{io::Reader as ImageReader, ImageFormat};
use std::env;
use image::imageops::{Lanczos3, blur};

const SIZE: u8 = 32;
const QUANTIZATION: u8 = 24;
const BLUR: u8 = 1;

fn get_image_from_url(url: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut response = get(url)?;

    let mut buffer = Vec::new();
    response.read_to_end(&mut buffer)?;

    let image = ImageReader::new(Cursor::new(buffer))
        .with_guessed_format()
        .unwrap()
        .decode()?;

    // Add alpha channel after every 3 bytes to the original image
    let image = image.into_rgba8();

    // Resize to SIZE x SIZE
    let image = image::imageops::resize(&image, SIZE as u32, SIZE as u32, Lanczos3);

    // Blur image
    let image = image::imageops::blur(&image, BLUR as f32);
    
    // Get image buffer
    let image_buffer = image.into_raw();


    Ok(image_buffer)
}

fn main() {
    let url: &str = &env::args().nth(1).expect("No URL provided!");
    match get_image_from_url(url) {
        Ok(image_data) => {
            println!("Image data: {:?}", image_data);
            // Quantize image
            // Label Connected Components
            // Compute CCV
        }
        Err(err) => eprintln!("Error retrieving image: {}", err),
    }
}