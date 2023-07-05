const Jimp = require('jimp');
const quantize = require('quantize');

const url = process.argv[2];
const quantized_level = 32;
const size = 32;
const blur = 1;

async function getImageBytesFromURL(url) {
    const image = await Jimp.read(url);
    image.resize(size, size);
    image.gaussian(blur);
    const pixels = [];
    image.scan(0, 0, image.bitmap.width, image.bitmap.height, function (x, y, idx) {
        const red = this.bitmap.data[idx + 0];
        const green = this.bitmap.data[idx + 1];
        const blue = this.bitmap.data[idx + 2];
        const alpha = this.bitmap.data[idx + 3];
        pixels.push([red, green, blue, alpha]);
    });
    const colorMap = quantize(pixels, quantized_level);
    // Return an array of the index of the color in the color map
    // For each pixel in the image, replace it with the index of the color in the color map
    const imageBytes = [];
    image.scan(0, 0, image.bitmap.width, image.bitmap.height, function (x, y, idx) {
        const red = this.bitmap.data[idx + 0];
        const green = this.bitmap.data[idx + 1];
        const blue = this.bitmap.data[idx + 2];
        const alpha = this.bitmap.data[idx + 3];
        const colorIndex = colorMap.map([red, green, blue, alpha]);
        imageBytes.push(colorIndex);
    }
    );
    return imageBytes;
}

const imageBytes = getImageBytesFromURL(url).then(imageBytes => {
    console.log(imageBytes);
});
