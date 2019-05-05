module.exports = {
      showOverallDecay: function (decodedFile, binningFactor, threshold) {
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
            let timeAxis = mathjs.range(0, (bins * binFactor * nanoResolution), (nanoResolution * binFactor))

            // Initializing array for nanotimes
            let histTmp = new Array(timeAxis.size()[0]).fill(0);
            let hist = new Array(timeAxis.size()[0]).fill(0);

            console.log(histTmp.length);
            console.log(hist.length);


            let x, y;

            for (x = 0; x < xPixels - 1; x++) {
                  for (y = 0; y < yPixels - 1; y++) {
                        if (decodedFile.nanoPixelArr[x][y].length >= threshold) {
                              histTmp = this.extractColumn(this.calcHist(decodedFile.nanoPixelArr[x][y], bins), 1);
                              histTmp.forEach(function (value, index) {
                                    hist[index] += value;
                              });
                              //hist = mathjs.add(hist, histTmp);
                              //nanotimesArr = [].concat(nanotimesArr, decodedFile.nanoPixelArr[x][y]);
                        };
                  };
                  console.log(histTmp);
            };

            console.log(hist);
            //hist[0] = timeAxis._data;
            //hist[1] = this.extractColumn(this.calcHist(nanotimesArr, bins), 1); // This needs to be reformatted so that only an array
            // nanotimesArr = null;


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
                        autorange: true//,
                        //type: "log"
                  },

            };

            Plotly.newPlot("histogram", plotData, layout, { staticPlot: true });
      },


      calcHist: function (data, bins) {
            const computeHistogram = require("compute-histogram");
            var hist = computeHistogram(data, bins);

            return (hist);
      },

      extractColumn: function (histArray, column) { // I was lazy and didn't implement the histogram calculation function myself. Therfore I need a function to extract the second column of the 2D array resulting from computeHistogram, because it containts the counts. The first column is the index.
            return histArray.map(x => x[column]);

      }
}