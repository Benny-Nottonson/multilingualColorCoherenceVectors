from io import BytesIO
from sys import argv
from PIL import Image
from numpy import ndarray, array, dot, argmin, empty, max as numpy_max, bincount, count_nonzero
from httpx import Client
from cv2 import cvtColor, COLOR_RGB2BGR, resize, blur
from functools import cache
from skimage.measure import label

url: str = argv[1]

client_get = Client().get

def get_image_from_url(url: str) -> ndarray:
    """Gets an image from a URL and converts it to BGR"""
    response_data = client_get(url, timeout=5)
    pil_image: Image = Image.open(BytesIO(response_data.content), mode="r").convert("RGB")
    rgb_image: ndarray = array(pil_image)
    return rgb_image

def resize_image(image: ndarray, size: int) -> ndarray:
    """Resizes an image to 16x16"""
    resized_image: ndarray = resize(image, (size, size))
    return resized_image

@cache
def find_minimum_macbeth(bgr_color: tuple[int, int, int], func: callable) -> int:
    """Finds the minimum Macbeth color for a given RGB color"""
    macbeth_colors = [
        [115, 82, 68], [194, 150, 130], [98, 122, 157], [87, 108, 67], [133, 128, 177],
        [103, 189, 170], [214, 126, 44], [80, 91, 166], [193, 90, 99], [94, 60, 108],
        [157, 188, 64], [224, 163, 46], [56, 61, 150], [70, 148, 73], [175, 54, 60],
        [231, 199, 31], [187, 86, 149], [8, 133, 161], [243, 243, 242], [200, 200, 200],
        [160, 160, 160], [122, 122, 121], [85, 85, 85], [52, 52, 52]
    ]
    color_distances = array([func(bgr_color, tuple(macbeth_color))
                             for macbeth_color in macbeth_colors])
    best = argmin(color_distances)
    return best

def lab_distance_3d(bgr_one: tuple[int, int, int], bgr_two: tuple[int, int, int]) -> float:
    """Estimates the distance between two BGR colors in LAB space"""
    l_one, a_one, b_one = bgr_to_lab(bgr_one)
    l_two, a_two, b_two = bgr_to_lab(bgr_two)
    return abs(l_one - l_two) + abs(a_one - a_two) + abs(b_one - b_two)

@cache
def bgr_to_lab(bgr_color: tuple[int, int, int]) -> tuple:
    """Converts a BGR color to a CIELAB color"""
    bgr_color: ndarray = array(bgr_color, dtype=float) / 255.0
    bgr_color: ndarray = _bgr_to_xyz(bgr_color)
    lab_color: tuple = _xyz_to_lab(bgr_color)
    return lab_color

def _bgr_to_xyz(normalized_bgr: ndarray) -> ndarray:
    """Converts a BGR color to a CIE XYZ color"""
    mask: ndarray = normalized_bgr > 0.04045
    normalized_bgr[mask] = ((normalized_bgr[mask] + 0.055) / 1.055) ** 2.4
    normalized_bgr[~mask] /= 12.92
    xyz_to_bgr_matrix: ndarray = array(
        [[0.1805, 0.3576, 0.4124], [0.0722, 0.7152, 0.2126], [0.9505, 0.1192, 0.0193]]
    )
    xyz_color: ndarray = dot(xyz_to_bgr_matrix, normalized_bgr)
    return xyz_color


def _xyz_to_lab(xyz: ndarray) -> tuple:
    """Converts a CIE XYZ color to a CIELAB color"""
    xyz_n_reference: ndarray = array([0.95047, 1.0, 1.08883])
    xyz_normalized: ndarray = (xyz / xyz_n_reference) ** (1 / 3)
    mask: ndarray = xyz_normalized <= 0.008856
    xyz_normalized[mask] = (7.787 * xyz_normalized[mask]) + (16 / 116)
    lab_color: tuple = (
        116 * xyz_normalized[1] - 16,
        500 * (xyz_normalized[0] - xyz_normalized[1]),
        200 * (xyz_normalized[1] - xyz_normalized[2]),
    )
    return lab_color

def quantize_image(img: ndarray) -> ndarray:
    """Converts an RGB image to a MAC image"""
    flattened_pixels: ndarray = img.reshape(-1, 3)
    macbeth_indices: ndarray = empty(flattened_pixels.shape[0], dtype="uint8")
    for i, pixel in enumerate(flattened_pixels):
        macbeth_indices[i] = find_minimum_macbeth(tuple(pixel), lab_distance_3d)
    mac_image: ndarray = macbeth_indices.reshape(img.shape[:2])
    return mac_image

def blur_image(img: ndarray) -> ndarray:
    """Blurs an image"""
    blurred_image: ndarray = blur(img, (1, 1))
    return blurred_image

def blob_extract(mac_image: ndarray) -> tuple[int, ndarray]:
    """Extracts blobs from a MAC image"""
    blob: ndarray = label(mac_image, connectivity=1) + 1
    n_blobs: int = numpy_max(blob)
    if n_blobs > 1:
        count: ndarray = bincount(blob.ravel(), minlength=n_blobs + 1)[2:]
        n_blobs += count_nonzero(count > 1)
    return n_blobs, blob
    
if __name__ == "__main__":
    image: ndarray = get_image_from_url(url)
    resized_image: ndarray = resize_image(image, 16)
    blurred_image: ndarray = blur_image(resized_image)
    size_threshold = round(0.01 * blurred_image.shape[0] * blurred_image.shape[1])
    quantized_image: ndarray = quantize_image(image)
    n_blobs, blob = blob_extract(array(quantized_image))
    table = [
        [quantized_image[i][j], table[blob[i][j] - 1][1] + 1] if blob[i][j] != 0 else [0, 0]
        for i in range(blob.shape[0])
        for j in range(blob.shape[1])
        for table in [[[0, 0] for _ in range(0, n_blobs)]]
    ]
    color_coherence_vector = [(0, 0) for _ in range(24)]
    for color_index, size in ((entry[0], entry[1]) for entry in table):
        color_coherence_vector[color_index] = (
            color_coherence_vector[color_index][0] + size * (size >= size_threshold),
            color_coherence_vector[color_index][1] + size * (size < size_threshold),
        )
    print(color_coherence_vector)