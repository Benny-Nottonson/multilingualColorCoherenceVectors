from io import BytesIO
from sys import argv
from PIL import Image
from numpy import ndarray, array
from httpx import Client
from cv2 import cvtColor, COLOR_RGBA2RGB, resize

url: str = argv[1]

client_get = Client().get

def get_image_from_url(url: str) -> ndarray:
    """Gets an image from a URL and converts it to BGR"""
    response_data = client_get(url, timeout=5)
    pil_image: Image = Image.open(BytesIO(response_data.content))
    bgr_image: ndarray = cvtColor(array(pil_image), COLOR_RGBA2RGB)
    return bgr_image

def resize_image(image: ndarray, size: int) -> ndarray:
    """Resizes an image to 16x16"""
    resized_image: ndarray = resize(image, (size, size))
    return resized_image

if __name__ == "__main__":
    image: ndarray = get_image_from_url(url)
    resized_image: ndarray = resize_image(image, 16)
    print(resized_image)