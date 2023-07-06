import Jimp from 'jimp';
import quantize from 'quantize';
import BlobExtraction from './ccl.js';

const url = process.argv[2];
const quantized_level = 8;
const size = 8;
const blur = 1;

function quantizeArray(pixels, quantized_level) {
    const colorMap = quantize(pixels, quantized_level);
    const palette = colorMap.palette();
    const labPalette = palette.map(color => rgb2lab(color));
    const labPixels = pixels.map(color => rgb2lab(color));
    const quantizedColors = labPixels.map(pixel => {
        let minDistance = Infinity;
        let minIndex = 0;
        for (let i = 0; i < labPalette.length; i++) {
            const distance = labDistance3d(pixel, labPalette[i]);
            if (distance < minDistance) {
                minDistance = distance;
                minIndex = i;
            }
        }
        return minIndex;
    });
    const quantizedColorsCopy = [...quantizedColors];
    BlobExtraction(quantizedColors, size, size);
    const nBlobs = Math.max(...quantizedColors);
    return [quantizedColorsCopy, quantizedColors, nBlobs];
}

labDistance3d.cache = {};
function labDistance3d(lab1, lab2) {
    const key = `${lab1[0]},${lab1[1]},${lab1[2]},${lab2[0]},${lab2[1]},${lab2[2]}`;
    if (labDistance3d.cache[key]) {
        return labDistance3d.cache[key];
    }
    const result = Math.abs(lab1[0] - lab2[0]) + Math.abs(lab1[1] - lab2[1]) + Math.abs(lab1[2] - lab2[2]);
    labDistance3d.cache[key] = result;
    return result;
}

rgb2lab.cache = {};
function rgb2lab(rgb) {
    const key = `${rgb[0]},${rgb[1]},${rgb[2]}`;
    if (rgb2lab.cache[key]) {
        return rgb2lab.cache[key];
    }
    let r = rgb.r || rgb[0] / 255;
    let g = rgb.g || rgb[1] / 255;
    let b = rgb.b || rgb[2] / 255;
    let x; let y; let z;
    r = (r > 0.04045) ? ((r + 0.055) / 1.055) ** 2.4 : r / 12.92;
    g = (g > 0.04045) ? ((g + 0.055) / 1.055) ** 2.4 : g / 12.92;
    b = (b > 0.04045) ? ((b + 0.055) / 1.055) ** 2.4 : b / 12.92;
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047;
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.00000;
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883;
    x = (x > 0.008856) ? x ** (1 / 3) : (7.787 * x) + 16 / 116;
    y = (y > 0.008856) ? y ** (1 / 3) : (7.787 * y) + 16 / 116;
    z = (z > 0.008856) ? z ** (1 / 3) : (7.787 * z) + 16 / 116;
    const result = [(116 * y) - 16, 500 * (x - y), 200 * (y - z)];
    rgb2lab.cache[key] = result;
    return result;
}

async function getImageBytesFromURL(url) {
    const image = await Jimp.read(url);
    image.resize(size, size, Jimp.RESIZE_BEZIER);
    image.gaussian(blur);
    const pixels = [];
    image.scan(0, 0, image.bitmap.width, image.bitmap.height, function (x, y, idx) {
        const red = this.bitmap.data[idx + 0];
        const green = this.bitmap.data[idx + 1];
        const blue = this.bitmap.data[idx + 2];
        pixels.push([red, green, blue]);
    });
    const [quantizedColors, blobs, nBlobs] = quantizeArray(pixels, quantized_level);
    return [quantizedColors, blobs, nBlobs];
}

const imageBytes = getImageBytesFromURL(url).then(imageBytes => {
    const [quantizedColors, blobs, nBlobs] = imageBytes;
    const blobs2d = [];
    for (let i = 0; i < size; i++) {
        blobs2d.push(blobs.slice(i * size, (i + 1) * size));
    }
    const table = [];
    const quantizedColors2d = [];
    for (let i = 0; i < size; i++) {
        quantizedColors2d.push(quantizedColors.slice(i * size, (i + 1) * size));
    }
    const size_threshold = Math.round(0.01 * size * size);
    for (let i = 0; i < blobs2d.length; i++) {
        for (let j = 0; j < blobs2d[i].length; j++) {
            if (blobs2d[i][j] !== 0) {
                table.push([quantizedColors2d[i][j], blobs2d[i][j]]);
            }
        }
    }
    const color_coherence_vector = [];
    for (let i = 0; i < quantized_level; i++) {
        color_coherence_vector.push([0, 0]);
    }
    for (let i = 0; i < table.length; i++) {
        const color_index = table[i][0];
        const size = table[i][1];
        color_coherence_vector[color_index] = [
            color_coherence_vector[color_index][0] + size * (size >= size_threshold),
            color_coherence_vector[color_index][1] + size * (size < size_threshold),
        ];
    }
    console.log(color_coherence_vector);
    return color_coherence_vector;
});
