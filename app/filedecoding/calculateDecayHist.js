module.exports = {
      showOverallDecay: function (decodedFile, binningFactor, threshold, histShift) {
            const mathjs = require("mathjs");
            const Plotly = require("plotly.js-dist");

            // getting neccessary infos from decoded file
            let xPixels = decodedFile.nanoPixelArr.length;
            let yPixels = decodedFile.nanoPixelArr[0].length;
            let syncRate = decodedFile.shortinfo.syncRate;
            let nanoResolution = mathjs.round(decodedFile.shortinfo.measRes, 12);
            let binFactor = binningFactor;

            // Calculating constants
            let bins = mathjs.round((1 / (syncRate * nanoResolution)) / binFactor);
            let binSteps = nanoResolution * binFactor;
            let timeAxis = mathjs.range(0, (bins * binFactor * nanoResolution), binSteps);
            let bin = 0;

            // Initializing array for nanotimes
            let hist = new Array(timeAxis.size()[0]).fill(0);

            let x, y, i;
            for (x = 0; x < xPixels; x++) {
                  for (y = 0; y < yPixels; y++) {
                        if (decodedFile.nanoPixelArr[x][y].length >= threshold) {
                              for (i = 0; i < decodedFile.nanoPixelArr[x][y].length; i++) {
                                    bin = Math.round(((decodedFile.nanoPixelArr[x][y][i] - histShift) * 1E-9) / binSteps);
                                    if (bin >= 0) hist[bin]++;
                              };
                        };
                  };
            };

            var plotData = [
                  {
                        x: timeAxis._data,
                        y: hist,
                        type: "scatter",
                  }
            ];

            var layout = {
                  autosize: false,
                  width: 800,
                  height: 600,
                  xaxis: {
                        autorange: true,
                  },
                  yaxis: {
                        autorange: true,
                        type: "linear"
                  },

            };

            Plotly.newPlot("histogram", plotData, layout, { staticPlot: true });

            hist = null;
            timeAxis = null;
      },


      calcHist: function (data, Nbins) {
            const computeHistogram = require("compute-histogram");
            var hist = computeHistogram(data, Nbins);

            return (hist);
      },

      extractColumn: function (histArray, column) { // I was lazy and didn't implement the histogram calculation function myself. Therfore I need a function to extract the second column of the 2D array resulting from computeHistogram, because it containts the counts. The first column is the index.
            return histArray.map(x => x[column]);
      }
}