# Psuedocode for an algorithm to computer the color coherence vector of an image from a url

## Input
- url of image
- size to resie image to (optional)
- blur radius (optional)
- color space to quantize (optional)

## Output
- color coherence vector of image

# Files and Functions
## Preprocessing
- `preprocess_image(url, size, blur_radius)` - get pixels from image, resize it, blur it

## Color Quantization
- `quantize_pixels(pixels, color_space)` - quantize pixels into color space

## Connectivity Analysis
- `compute_connectivity(pixels)` - compute connectivity of pixels

## Color Coherence Vector
- `compute_ccv(pixels, labels)` - compute color coherence vector from pixels

```mermaid
graph TD;
    subgraph Preprocessing
        preprocess_image --> quantize_pixels
        quantize_pixels --> compute_connectivity
    end
    compute_connectivity --> compute_ccv
```