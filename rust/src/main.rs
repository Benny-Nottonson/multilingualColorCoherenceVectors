use reqwest::blocking::get;
use std::io::{Read, Cursor};
use image::{io::Reader as ImageReader, ImageFormat};

fn get_image_from_url(url: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut response = get(url)?;

    let mut buffer = Vec::new();
    response.read_to_end(&mut buffer)?;

    let image = ImageReader::new(Cursor::new(buffer))
        .with_guessed_format()
        .unwrap()
        .decode()?;

    let mut image_buffer = Cursor::new(Vec::new());
    image.write_to(&mut image_buffer, ImageFormat::Png)?;
    let image_buffer = image_buffer.into_inner();

    Ok(image_buffer)
}

fn main() {
    let url = "https://i.redd.it/w3kr4m2fi3111.png";
    match get_image_from_url(url) {
        Ok(image_data) => {
            println!("Image retrieved successfully!");
            println!("{:?}", image_data);
        }
        Err(err) => eprintln!("Error retrieving image: {}", err),
    }
}