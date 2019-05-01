module.exports = {

      calcHist: function (data, binningFactor) {

            const computeHistogram = require("compute-histogram");

            var hist = computeHistogram(data, 100); // Let's use 100 for now!
            var phasorCoords = this.calculatePhasor(hist);

            return (phasorCoords);
      },

      calculatePhasor: function (histogram) {
            var g = 0, s = 0, i;

            for (i = 0; i < histogram.length; i++) {
                  console.log(histogram[i][1]);
            };
            console.log("lol");
      },

      phasorTransform: function (decodedFile, binningFactor) {

            // getting neccessary infos from decoded file
            var xPixels = decodedFile.shortinfo.pixelX;
            var yPixels = decodedFile.shortinfo.pixelY
            var syncRate = decodedFile.shortinfo.syncRate;
            var fileBinningFactor = decodedFile.shortinfo.measRes;
            var bins = binningFactor;

            // Calculating constants
            var angularFrequency = 2 * Math.PI * syncRate;
            var timeAxis = new Array(100)
            Math

            // Init array for phasor coordinates
            var j;
            var i;

            let phasorArr = new Array(decodedFile.shortinfo.pixelX); // Assuming a square image!

            for (i = 0; i < phasorArr.length; i++) {
                  phasorArr[i] = new Array(decodedFile.shortinfo.pixelY);
                  for (j = 0; j < phasorArr[i].length; j++) {
                        phasorArr[i][j] = new Array(2); // 0: g coordinate; 1: s coordinate
                  };
            };



            this.calcHist(decodedFile.nanoPixelArr[64][64], 1);

            var x, y;
            var length = decodedFile.nanoPixelArr.length;
            for (x = 0; x < length; x++) {
                  for (y = 0; y < decodedFile.nanoPixelArr[0].length; y++) {
                        phasorArr[x][y] = decodedFile.nanoPixelArr[x][y];
                  };
            };

            //console.log(phasorArr[12][12]);
      }
};