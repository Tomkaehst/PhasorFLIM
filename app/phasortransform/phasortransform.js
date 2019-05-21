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
            // var polar = [mathjs.sqrt(result[0] ** 2 + result[1] ** 2), mathjs.multiply((360) / (2 * Math.PI), mathjs.atan2(result[1], result[0]))];
            return (result);
      },


      phasorTransform: function (decodedFile, binningFactor, threshold, histShiftLeft, histShiftRight, histOffset, freqUp) {

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
            var hist = new Array(timeAxis.size()[0]).fill(0);
            var i, bin;

            // Start showing progressbar
            ipc.send("start-progressbar");

            // Calculating hist for each pixel and g/s coordinates
            for (x = 0; x < xPixels - 1; x++) {
                  for (y = 0; y < yPixels - 1; y++) {
                        // Only evaluate pixels that have > counts than user-defined count threshold
                        if (decodedFile.nanoPixelArr[x][y].length > threshold) {
                              for (i = 0; i < decodedFile.nanoPixelArr[x][y].length; i++) {
                                    if (decodedFile.nanoPixelArr[x][y][i] <= (histShiftRight)) {
                                          bin = Math.round(((decodedFile.nanoPixelArr[x][y][i] - histShiftLeft) * 1E-9) / binSteps);
                                    };

                                    if (bin >= 0) hist[bin]++;
                              };

                              // Subtracting user-defined count offset
                              hist.forEach((bin, index) => {
                                    hist[index] = (bin - histOffset);
                              });

                              // Calculate phasor 
                              phasorArr[x][y] = this.calculatePhasor(hist, timeAxis, angularFrequency); // g and s coordinates as array [g, s]
                              phasorArr[x][y].push(x);
                              phasorArr[x][y].push(y);
                              hist.fill(0);
                        };
                  };
                  // Updating progressbar
                  ipc.send("update-progressbar", ["Calculating Phasors ...", Math.round((x / xPixels) * 100)]);
            };

            ipc.send("end-progressbar");
            return (phasorArr);
      },

      showPhasor: function (decodedFile, frequencyMultiplicator) {
            let phasorArr = decodedFile.phasors;

            const Plotly = require("plotly.js-dist");
            let plotArea = document.getElementById("plotArea");


            // Pushing the phasor coordinates into an array for visualization in plotlyjs; calculating mean lifetime also
            let angularFrequency = 2 * Math.PI * decodedFile.shortinfo.syncRate * frequencyMultiplicator;
            let gAvg = 0;
            let sAvg = 0;


            var g = new Array();
            var s = new Array();
            let x, y;
            for (x = 0; x < phasorArr.length; x++) {
                  for (y = 0; y < phasorArr[0].length; y++) {
                        g.push(phasorArr[x][y][0]);
                        s.push(phasorArr[x][y][1]);
                        if (phasorArr[x][y][0] != undefined && phasorArr[x][y][1] != undefined) {
                              gAvg += phasorArr[x][y][0] * decodedFile.nanoPixelArr[x][y].length; // Multiplied with number of photons in pixel for weighting, later divided by number of overall photons
                              sAvg += phasorArr[x][y][1] * decodedFile.nanoPixelArr[x][y].length;
                        };
                  };
            };

            let lifetimeFromPhasors = (1 / angularFrequency) * ((sAvg / decodedFile.shortinfo.numRec) / (gAvg / decodedFile.shortinfo.numRec));
            // let lifetimeFromPhasors = (1 / angularFrequency) * (sAvg / gAvg);
            document.getElementById("avgLifetime").innerHTML = " " + Number((lifetimeFromPhasors * 1E9).toFixed(2)) + " ns"

            var points = {
                  x: g,
                  y: s,
                  mode: 'markers',
                  marker: {
                        color: 'rgb(100, 100, 100)',
                        size: 0.1,
                        opacity: 0
                  },
                  type: "scattergl"
            };

            // Defining contour plot
            var density = {
                  x: g,
                  y: s,
                  ncontours: 10,
                  colorscale: 'Hot',
                  reversescale: true,
                  showscale: true,
                  type: 'histogram2dcontour'
            };

            // Adding lifetime reference points to plot
            var lifetimeRefs = this.calculateReferencePoints([1E-9, 1.5E-9, 2E-9, 2.5E-9, 3E-9, 5E-9, 10E-9], angularFrequency);
            var refPoints = {
                  type: "scattergl",
                  mode: "markers+text",
                  x: lifetimeRefs[0],
                  y: lifetimeRefs[1],
                  color: "black",
                  text: ["1 ns", "1.5 ns", "2 ns", "2.5 ns", "3 ns", "5 ns", "10 ns"],
                  textposition: "bottom",
            };

            var plotData = [points, density, refPoints];

            var layout = {
                  hovermode: false,
                  autosize: false,
                  width: 800,
                  height: 600,
                  xaxis: { range: [0, 1] },
                  yaxis: {
                        range: [0, 0.6]
                  },
                  plot_bgcolor: "rgba(0, 0, 0, 0)",
                  paper_bgcolor: "rgba(0, 0, 0, 0)",
                  shapes: [{
                        type: 'circle',
                        xref: 'x',
                        yref: 'y',
                        x0: 0,
                        y0: -0.5,
                        x1: 1,
                        y1: 0.5,
                        line: {
                              color: 'black'
                        }
                  }],
            };

            Plotly.newPlot(plotArea, plotData, layout);

            // Check if user interacts with phasor plot and perform image colorization based on selection
            // const phasorPlot = document.getElementById("plotArea")
            // phasorPlot.on("plotly_selected", (selectedData) => {
            //       let selectedCoordinates = new Array(selectedData.points.length);
            //       // Because all histogram and phasor calculations are based on the nanotime array with x and y pixels, it is safe to assume, that the index number returned by plotly (based on the index of the phasor coordinates arrays) can be mapped back to the pixel in x and y.
            //       selectedData.points.forEach((point, index) => {
            //             selectedCoordinates[index] = point.pointIndex;
            //       });
            //       const intImg = require("../render/showintensityimage.js");
            //       intImg.colorizeFromPhasorSelection(decodedFile, selectedCoordinates);
            // });



            // Dereferencing g and s coordinates for memory 
            g = null;
            s = null;
      },

      calculateReferencePoints(lifetimes, angularFrequency) {
            var refG = [];
            var refS = [];

            lifetimes.forEach((lifetime) => {
                  refG.push((1) / (1 + (angularFrequency ** 2) * (lifetime ** 2)));
                  refS.push((angularFrequency * lifetime) / (1 + (angularFrequency ** 2) * lifetime ** 2));
            });

            return ([refG, refS]);
      },

      lifetimeDistributionFromPhasors: function (decodedFile, tauStart, tauEnd, frequencyMultiplicator) {

            // Initializing variables
            const mathjs = require("mathjs");
            let lifetimeRange = (tauStart - tauEnd);
            let bins = Math.round(lifetimeRange * 100); // 100 bins per ns
            var lifetimeHist = new Array(2); // [0] is for the x-axis, [1] for the lifetime density
            lifetimeHist[0] = mathjs.range(tauEnd, tauStart, 0.01)
            lifetimeHist[1] = new Array(bins).fill(0);
            var x, y, tmpLifetime, tmpBin;

            // Constants for calculating lifetime
            let angularFrequency = 2 * Math.PI * decodedFile.shortinfo.syncRate * frequencyMultiplicator;
            // let lifetimeFromPhasors = (1 / angularFrequency) * ((sAvg / decodedFile.shortinfo.numRec) / (gAvg / decodedFile.shortinfo.numRec));

            for (x = 0; x < decodedFile.phasors.length; x++) {
                  for (y = 0; y < decodedFile.phasors[0].length; y++) {
                        if (decodedFile.phasors[x][y][0] != undefined || decodedFile.phasors[x][y][1] != undefined) {
                              tmpLifetime = (1 / angularFrequency) * (decodedFile.phasors[x][y][1] / decodedFile.phasors[x][y][0]);
                              tmpBin = Math.floor((((tmpLifetime * 1E9) - tauEnd) / lifetimeRange) * lifetimeHist[0].size());

                              lifetimeHist[1][tmpBin]++;
                        };

                  };
            };

            return (lifetimeHist);
      },

      showLifetimeHist: function (decodedFile) {
            const Plotly = require("plotly.js-dist");

            var histArea = document.getElementById("lifetimeHistArea");

            var histData = {
                  x: decodedFile.lifetimeHist[0]._data,
                  y: decodedFile.lifetimeHist[1],
                  //mode: "markers",
                  type: "bar",
                  autobinx: false
            };

            var layout = {
                  width: 800,
                  height: 600,
                  bargap: 0.05,
                  title: "Lifetime Distribution",
                  xaxis: {
                        title: "Lifetime (ns)"
                  },
                  yaxis: {
                        title: "Counts"
                  }
            };

            Plotly.newPlot(histArea, [histData], layout);
      }

};