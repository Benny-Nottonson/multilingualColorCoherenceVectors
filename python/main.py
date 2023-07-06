from numpy import ndarray, array, count_nonzero, bincount, max as numpy_max
from skimage.measure import label
from io import BytesIO
from sys import argv
from PIL import Image, ImageFilter
from httpx import Client

url: str = argv[1]
quantized_level = 8
size = 8
blur = 1

client = Client()

def get_image_from_url(url: str) -> Image:
    """Gets an image from a URL and converts it to rgb"""
    response_data = client.get(url, timeout=5)
    pil_image: Image = Image.open(BytesIO(response_data.content), mode="r").convert("RGB")
    pil_image = pil_image.filter(ImageFilter.GaussianBlur(blur))
    pil_image = pil_image.resize((size, size), Image.Resampling.LANCZOS)
    pil_image = pil_image.quantize(quantized_level)
    return pil_image

def blob_extract(mac_image: ndarray) -> tuple[int, ndarray]:
    """Extracts blobs from a quantized image"""
    blob: ndarray = label(mac_image, connectivity=1) + 1
    n_blobs: int = numpy_max(blob)
    if n_blobs > 1:
        count: ndarray = bincount(blob.ravel(), minlength=n_blobs + 1)[2:]
        n_blobs += count_nonzero(count > 1)
    return n_blobs, blob

if __name__ == "__main__":
    image: Image = get_image_from_url(url)
    image_array = array(image)
    size_threshold = round(0.01 * size * size)
    n_blobs, blob = blob_extract(image_array)
    table = [
        [image_array[i][j], table[blob[i][j] - 1][1] + 1] if blob[i][j] != 0 else [0, 0]
        for i in range(blob.shape[0])
        for j in range(blob.shape[1])
        for table in [[[0, 0] for _ in range(0, n_blobs)]]
    ]
    color_coherence_vector = [(0, 0) for _ in range(quantized_level)]
    for color_index, size in ((entry[0], entry[1]) for entry in table):
        color_coherence_vector[color_index] = (
            color_coherence_vector[color_index][0] + size * (size >= size_threshold),
            color_coherence_vector[color_index][1] + size * (size < size_threshold),
        )
    print(color_coherence_vector)
