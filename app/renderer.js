// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.

const ipc = require("electron").ipcRenderer;
const chart = require("chart.js");

// Loading script for calculation of intensity image; requires PTUReader.js; --> provide filepath to imgCalc.calculateIntensityImage()
const imgCalc = require("./filedecoding/intensityImage.js");
const PTUReader = require("./filedecoding/PTUReader.js");
const intImg = require("./render/showintensityimage.js");
const nanoToPixel = require("./filedecoding/nanotimeToPixels");
const phasorCalc = require("./phasortransform/phasortransform.js");

// Select elements from GUI
const ptuFileBtn = document.getElementById("ptuSubmit");
const processPtuBtn = document.getElementById("processPtu");
const imageCanvas = document.getElementById("outputImg");
const phasorBtn = document.getElementById("makePhasor");


// Initializing variables
let fileDecoded; // JavaScript object; holds decoded ptu events and is appended with intensity image and phasor coordinates


// Listening for button clicks on the .ptu file button and sending request to main process via IPC to get the filepath, via channel "ptu-filepath"
ptuFileBtn.addEventListener("click", function (event) {
      ipc.send("ptu-filepath");
});



// Listening for filepath on "selectedptu" channel
let fp = "";
ipc.on("selectedptu", function (event, path) {
      fp = path[0];
      fileDecoded = PTUReader.decodePTU(fp);
});


// Chose PTU file, decode it, calculate intensity image -> decoded ptu saved as "fileDecoded" in RAM
processPtuBtn.addEventListener("click", function (event) {
      if (fileDecoded) {
            var channelSelected = document.getElementById("channelSelector").value;
            var intensityMultiplicator = document.getElementById("intensityMultiplicator").value;
            var binningFactor = document.getElementById("binningFactor").value;
            let intImageArr = imgCalc.calculateIntensityImage(fileDecoded, channelSelected, binningFactor);
            intImg.showImage(intImageArr, imageCanvas, intensityMultiplicator);
            fileDecoded.intImage = intImageArr; // Adding the intensity image data to fileDecoded
      } else {
            alert("A .ptu file has to be loaded first.");
      };

});


// Calculate phasor transform 
phasorBtn.addEventListener("click", function () {

      if (fileDecoded == undefined) {
            alert("You need to load a .PTU first!")
      } else {
            // Calculating phasors
            var channelSelected = document.getElementById("channelSelector").value;
            var binningFactor = document.getElementById("binningFactor").value;
            fileDecoded.nanoPixelArr = nanoToPixel.attachNanotimes(fileDecoded, channelSelected, binningFactor);
            fileDecoded.phasors = phasorCalc.phasorTransform(fileDecoded, 10);

            // Rearranging phasor coordinates for Charts.js which expects: [{x: 1, y: 1}, {x: 1, y: 1}, ...]
            let x, y;
            let phasorData = new Array();

            for (x = 0; x < fileDecoded.phasors.length - 1; x++) {
                  for (y = 0; y < fileDecoded.phasors[0].length - 1; y++) {
                        phasorData.push({ x: fileDecoded.phasors[x][y][0], y: fileDecoded.phasors[x][y][1] })
                  };
            };

            // There seem to be a bug in chartsjs; I need fixed axes
            phasorData.push({ x: 1, y: 1 });
            phasorData.push({ x: 0, y: 0 });

            // Showing plot
            let pltCtx = document.getElementById("plot").getContext("2d");
            let phasorPlot = new chart.Chart(pltCtx, {
                  type: "scatter",
                  data: {
                        datasets: [{
                              label: "Phasor Transform",
                              data: phasorData
                        }]
                  },
                  options: {
                        scales: {
                              xAxes: {
                                    ticks: {
                                          beginAtZero: true,
                                          min: 0,
                                          max: 1,
                                          stepSize: 0.1,
                                    }
                              },
                              yAxes: {
                                    ticks: {
                                          beginAtZero: true,
                                          min: 0,
                                          max: 1,
                                          stepSize: 0.1,
                                    }
                              }
                        }
                  }
            });
      };

});