/*
      Reconstructing the intensity image of the .ptu file decoded by PTUReader.js which outputs:
      - macrotime array: events on experiment timescale
      - nanotime array: events relative to last sync pulse
      - markers array: encodes event type (1, 2: photon in channel 1/2; 6: line start; 7: line stop; 63: overflow)
      - shortinfo: JavaScript Object with relevant information for image reconstruction from file header
      - fullinfo: Complete header from .ptu file
*/


module.exports = {

      /*
            The FLIM image encoded in the .ptu file is visualized with this function according to the pixel photon count / light intensity at a pixel. It receives a reference to the nanotimeArray, which is a 3D array: x and y dimensions according to the original image dimension / user-selected binning factor; each pixel habors an array of nanotimes detected over the scanning period of the experiment. The pixel intensity is just the number of nanotimes in this nanotime array, as it corresponds to the number of detected photons.
            The resulting imgArr (2D array of x and y; each pixel encoded an integer = number of photon counts) is used in showintensityimage.showImage(), where the imgArr is encoded as an HTML canvas imageData object (RGB-alpha, intensity is alpha!).
      */
      calculateIntensityImage: function (nanotimeArray) {

            let pixelX = nanotimeArray.length;
            let pixelY = nanotimeArray[0].length;

            // Initializing 2D array for image reconstruction
            let imgArr = new Array(pixelX).fill(0);

            var x, y;
            for (x = 0; x < pixelX; x++) {
                  imgArr[x] = new Array(pixelY).fill(0);
                  for (y = 0; y < pixelY; y++) {
                        imgArr[x][y] = nanotimeArray[x][y].length;
                  };
            };

            return (imgArr);

      }
};


