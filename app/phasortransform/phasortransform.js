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


      phasorTransform: function (decodedFile, binningFactor, threshold, histShift, freqUp) {

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
            let binSteps = nanoResolution * binFactor;
            let angularFrequency = 2 * Math.PI * syncRate * freqMult;
            let timeAxis = mathjs.range(0, (bins * binFactor * nanoResolution), binSteps);



            // Initializing 3D array for phasor coordinates; 2D for x-y pos; at each x-y array with two values for g and s coordinate
            let phasorArr = new Array(xPixels);
            let x, y;

            for (x = 0; x < xPixels; x++) {
                  phasorArr[x] = new Array(yPixels);
                  for (y = 0; y < yPixels; y++) {
                        phasorArr[x][y] = []; // Holds g coordinate at 0 and s coordinate at 1; corresponding x and y cooridate at array position 2 and 3 respectively
                  };
            };



            // Calculating histogram for each pixel
            let hist = new Array(timeAxis.size()[0]).fill(0);
            let i;

            console.log(hist.length);
            console.log(timeAxis.size());

            for (x = 0; x < xPixels - 1; x++) {
                  for (y = 0; y < yPixels - 1; y++) {
                        if (decodedFile.nanoPixelArr[x][y].length > threshold) {
                              for (i = 0; i < decodedFile.nanoPixelArr[x][y].length; i++) {
                                    bin = Math.round(((decodedFile.nanoPixelArr[x][y][i] - histShift) * 1E-9) / binSteps);
                                    if (bin >= 0) hist[bin]++;
                              };

                              phasorArr[x][y] = this.calculatePhasor(hist, timeAxis, angularFrequency); // g and s coordinates as array [g, s]
                              phasorArr[x][y].push(x);
                              phasorArr[x][y].push(y);
                              hist.fill(0);
                        };
                  };
            };
            return (phasorArr);
      },

      showPhasor(decodedFile) {
            let phasorArr = decodedFile.phasors;

            const Plotly = require("plotly.js-dist");
            let plotArea = document.getElementById("plotArea");

            var g = new Array();
            var s = new Array();
            let x, y;
            for (x = 0; x < phasorArr.length; x++) {
                  for (y = 0; y < phasorArr[0].length; y++) {
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
                        type: "scattergl",
                        mode: "markers"
                  }
            ];

            var layout = {
                  autosize: false,
                  width: 800,
                  height: 600,
                  xaxis: { range: [0, 1] },
                  yaxis: { range: [0, 0.6] },
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

            Plotly.newPlot(plotArea, plotData, layout);

            // Check if user interacts with phasor plot and perform image colorization based on selection
            const phasorPlot = document.getElementById("plotArea")
            phasorPlot.on("plotly_selected", (selectedData) => {
                  let selectedCoordinates = new Array(selectedData.points.length);
                  // Because all histogram and phasor calculations are based on the nanotime array with x and y pixels, it is safe to assume, that the index number returned by plotly (based on the index of the phasor coordinates arrays) can be mapped back to the pixel in x and y.
                  selectedData.points.forEach((point, index) => {
                        selectedCoordinates[index] = point.pointIndex;
                  });
                  const intImg = require("../render/showintensityimage.js");
                  console.log(selectedCoordinates);
                  intImg.colorizeFromPhasorSelection(decodedFile, selectedCoordinates);
            });

            g = null;
            s = null;
      }
};