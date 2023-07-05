from io import BytesIO
from sys import argv
from PIL import Image
from numpy import ndarray, array, argmin, empty, max as numpy_max, bincount, count_nonzero
from httpx import Client
from cv2 import resize, blur
from functools import cache
from skimage.measure import label
from skimage.color import rgb2lab

url: str = argv[1]

client_get = Client().get

def get_image_from_url(url: str) -> ndarray:
    """Gets an image from a URL and converts it to rgb"""
    response_data = client_get(url, timeout=5)
    pil_image: Image = Image.open(BytesIO(response_data.content), mode="r").convert("RGB").quantize(24)
    rgb_image: ndarray = array(pil_image)
    return rgb_image

def resize_image(image: ndarray, size: int) -> ndarray:
    """Resizes an image to 16x16"""
    resized_image: ndarray = resize(image, (size, size))
    return resized_image

@cache
def find_minimum_macbeth(rgb_color: tuple[int, int, int]) -> int:
    """Finds the minimum Macbeth color for a given RGB color"""
    macbeth_colors_lab = [
        (38.01556819050297, 11.799246065430925, 13.659810862228817),
        (65.66584592032572, 13.677966707062506, 16.891497135258792),
        (50.62872612858402, 0.3762204345665876, -21.60668785772295),
        (42.99827414912467, -15.875497785250769, 20.448220821512532),
        (55.68426392278387, 12.769622676794935, -25.17743656853377),
        (70.99555652720578, -30.633920904301004, 1.5313021653773573),
        (61.132774518070505, 28.10840041331891, 56.13159225919361),
        (41.1219051456942, 17.416808162968035, -41.887847715629746),
        (51.32530009287757, 42.103298772955874, 14.875103773761023),
        (31.100148909436427, 24.360449682691687, -22.10563091981519),
        (71.89619196717393, -28.105371212539087, 56.95643588819582),
        (71.03534310675323, 12.604144827425168, 64.91630276853245),
        (30.352217643249205, 26.44171827900474, -49.67478949861708),
        (55.03414375826084, -40.13717467074795, 32.294606416704895),
        (41.34067187464068, 49.31214182927615, 24.65453708377111),
        (80.70247272634805, -3.664136504373472, 77.55076396301426),
        (51.14074495202793, 48.15685180402457, -15.293832639161952),
        (51.15181402648304, -19.723109447744026, -23.37811709196305),
        (95.81673513861851, -0.17120059258257658, 0.47062215313316),
        (80.60408285838321, 0.0043809118435156336, -0.008667871726619758),
        (65.86781342007546, 0.0037126347334770493, -0.007345649213430505),
        (51.1947408046985, -0.1968062646886537, 0.5399645509152728),
        (36.14585083971984, 0.0023647693635220346, -0.00467882446352208),
        (21.704275932542863, 0.001709856396275855, -0.003383043631877136),
    ]
    color_distances = array([lab_distance_3d(rgb_color, macbeth_color)
                             for macbeth_color in macbeth_colors_lab])
    best = argmin(color_distances)
    return best

def lab_distance_3d(rgb_one: tuple[int, int, int], rgb_two: tuple[int, int, int]) -> float:
    """Estimates the distance between two rgb colors in LAB space"""
    l_one, a_one, b_one = rgb2lab(rgb_one)
    l_two, a_two, b_two = rgb_two
    return abs(l_one - l_two) + abs(a_one - a_two) + abs(b_one - b_two)

@cache
def rgb2labCached(rgb_color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Converts an RGB color to a LAB color"""
    return rgb2lab(rgb_color)

def quantize_image(img: ndarray) -> ndarray:
    """Converts an RGB image to a MAC image"""
    flattened_pixels: ndarray = img.reshape(-1, 3)
    macbeth_indices: ndarray = empty(flattened_pixels.shape[0], dtype="uint8")
    for i, pixel in enumerate(flattened_pixels):
        macbeth_indices[i] = find_minimum_macbeth(tuple(pixel))
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