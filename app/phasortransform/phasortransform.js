module.exports = {
      calculatePhasor: function (histogram) {

      },

      calcHist: function (decay, binningFactor) {
            var computeHistogram = require("compute-histogram");

            var hist = computeHistogram(testArr, 10);

            console.log("testArr: " + testArr + "\n hist: " + hist);
      },

      phasorTransform: function (decodedFile, binningFactor) {


            
            // Init g coordinates

            var gArr

            // Init s coordinates


            fileBinningFactor = decodedFile.shortinfo.measRes;
            var bins = binningFactor;

            var x, y;

            for (x = 0; x < decodedFile.nanoPixelArr.length; x++) {
                  for (y = 0; y < decodedFile.nanoPixelArr[0].length; y++) {

                  };
            };

      }
};