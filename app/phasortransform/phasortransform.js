module.exports = {

      calcHist: function (data, bins) {
            const computeHistogram = require("compute-histogram");
            var hist = computeHistogram(data, bins); // Let's use 100 for now!

            return (hist);
      },

      calculatePhasor: function (histogram) {
            var g = 0, s = 0, i;

            for (i = 0; i < histogram.length; i++) {
                  console.log(histogram[i][1]);
            };
            console.log("lol");
      },

      phasorTransform: function (decodedFile, binningFactor) {

            const mathjs = require("mathjs");

            // getting neccessary infos from decoded file
            let xPixels = decodedFile.shortinfo.pixelX;
            let yPixels = decodedFile.shortinfo.pixelY
            let syncRate = decodedFile.shortinfo.syncRate;
            let nanoResolution = mathjs.round(decodedFile.shortinfo.measRes, 12);
            let freqMult = 1;
            let binFactor = binningFactor;

            // Calculating constants
            let bins = mathjs.round(1 / (syncRate * nanoResolution) * freqMult) / binFactor;
            let angularFrequency = 2 * Math.PI * syncRate * freqMult;

            // Calculating histogram for each pixel

            var hist = this.calcHist(decodedFile.nanoPixelArr[64][64], bins);


            console.log(hist);

      }
};