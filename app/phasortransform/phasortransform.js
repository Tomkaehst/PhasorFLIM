module.exports = {

      calcHist: function (data, bins) {
            const computeHistogram = require("compute-histogram");
            var hist = computeHistogram(data, bins);

            return (hist);
      },

      extractColumn: function (histArray, column) { // I was lazy and didn't implement the histogram calculation function myself. Therfore I need a function to extract the second column of the 2D array resulting from computeHistogram, because it containts the counts. The first column is the index.
            return histArray.map(x => x[column]);

      },

      calculatePhasor: function (histogram, timeAxis, angularFrequency) {
            const mathjs = require("mathjs");
            var gUpper = mathjs.dotMultiply(mathjs.cos(mathjs.multiply(timeAxis, angularFrequency)), histogram);
            var sUpper = mathjs.dotMultiply(mathjs.sin(mathjs.multiply(timeAxis, angularFrequency)), histogram);
            var histSum = mathjs.sum(histogram);
            var gSum = mathjs.sum(gUpper);
            var sSum = mathjs.sum(sUpper);
            var result = [(gSum / histSum), (sSum / histSum)];
            return (result);
      },


      phasorTransform: function (decodedFile, binningFactor, threshold, freqUp) {

            const mathjs = require("mathjs");

            // getting neccessary infos from decoded file
            let xPixels = decodedFile.nanoPixelArr.length;
            let yPixels = decodedFile.nanoPixelArr[0].length;
            let syncRate = decodedFile.shortinfo.syncRate;
            let nanoResolution = mathjs.round(decodedFile.shortinfo.measRes, 12);
            let freqMult = freqUp;
            let binFactor = binningFactor;

            // Calculating constants
            let bins = mathjs.round((1 / (syncRate * nanoResolution)) / binFactor);
            let angularFrequency = 2 * Math.PI * syncRate * freqMult;
            let timeAxis = mathjs.range(0, (bins * binFactor * nanoResolution), (nanoResolution * binFactor))



            // Initializing 3D array for phasor coordinates; 2D for x-y pos; at each x-y array with two values for g and s coordinate
            let phasorArr = new Array(xPixels);
            let x, y;

            for (x = 0; x < xPixels - 1; x++) {
                  phasorArr[x] = new Array(yPixels);
                  for (y = 0; y < yPixels - 1; y++) {
                        phasorArr[x][y] = []; // Holds g coordinate at 0 and s coordinate at 1
                  };
            };



            // Calculating histogram for each pixel
            let histTmp = [];

            for (x = 0; x < xPixels - 1; x++) {
                  for (y = 0; y < yPixels - 1; y++) {
                        if (decodedFile.nanoPixelArr[x][y].length > threshold) {
                              histTmp = this.extractColumn(this.calcHist(decodedFile.nanoPixelArr[x][y], bins), 1); // This needs to be reformatted so that only an array
                              phasorArr[x][y] = this.calculatePhasor(histTmp, timeAxis, angularFrequency); // g and s coordinates as array [g, s]
                        };
                  };
            };

            return (phasorArr);
      },

      showPhasor(phasorArr) {
            const Plotly = require("plotly.js-dist");

            var g = new Array();
            var s = new Array();
            let x, y;
            for (x = 0; x < phasorArr.length - 1; x++) {
                  for (y = 0; y < phasorArr[0].length - 1; y++) {
                        g.push(phasorArr[x][y][0]);
                        s.push(phasorArr[x][y][1]);
                  };
            };

            var plotData = [
                  {
                        x: g,
                        y: s,
                        colorscale: "Greys",
                        reversescale: true,
                        type: "scatter",
                        mode: "markers",
                        contours: {
                              coloring: "heatmap"
                        }
                  }
            ];

            var layout = {
                  autosize: false,
                  width: 800,
                  height: 600,
                  xaxis: { range: [0, 1] },
                  yaxis: { range: [0, 0.6] },
                  showlegend: false,
                  plot_bgcolor: "transparent",
                  shapes: [{
                        type: 'circle',
                        xref: 'x',
                        yref: 'y',
                        x0: 0,
                        y0: -1,
                        x1: 1,
                        y1: 0.5,
                        line: {
                              color: 'black'
                        }
                  }],
            };

            Plotly.newPlot("plotArea", plotData, layout, { staticPlot: true });
      },

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
            let nanotimesArr = [];
            let hist = new Array();
            let x, y;

            for (x = 0; x < xPixels - 1; x++) {
                  for (y = 0; y < yPixels - 1; y++) {
                        if (decodedFile.nanoPixelArr[x][y].length >= threshold) {
                              //histTmp = this.extractColumn(this.calcHist(decodedFile.nanoPixelArr[x][y], bins), 1); // This needs to be reformatted so that only an array
                              nanotimesArr = nanotimesArr.concat(decodedFile.nanoPixelArr[x][y]);
                        };
                  };
            };
            hist[0] = this.extractColumn(this.calcHist(nanotimesArr, bins), 1); // This needs to be reformatted so that only an array
            hist[1] = timeAxis;
            nanotimesArr = null;


            var plotData = [
                  {
                        x: hist[1],
                        y: hist[0],
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
                        type: "log"
                  },

            };

            Plotly.newPlot("plotArea", plotData, { staticPlot: true });
            console.log(timeAxis);
      }
};