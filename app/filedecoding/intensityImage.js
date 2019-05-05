/*
      Reconstructing the intensity image of the .ptu file decoded by PTUReader.js which outputs:
      - macrotime array: events on experiment timescale
      - nanotime array: events relative to last sync pulse
      - markers array: encodes event type (1, 2: photon in channel 1/2; 6: line start; 7: line stop; 63: overflow)
      - shortinfo: JavaScript Object with relevant information for image reconstruction from file header
      - fullinfo: Complete header from .ptu file
*/


module.exports = {
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


