// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
const ipc = require("electron").ipcRenderer;

// Loading script for calculation of intensity image; requires PTUReader.js; --> provide filepath to imgCalc.calculateIntensityImage()
const imgCalc = require("./filedecoding/intensityImage.js");
// const PTUReader = require("./filedecoding/PTUReader.js");
const PTUReader = require("./filedecoding/PTUReaderBitwise.js");
const intImg = require("./render/showintensityimage.js");
const nanoToPixel = require("./filedecoding/nanotimeToPixels");
const histCalc = require("./filedecoding/calculateDecayHist.js");
const phasorCalc = require("./phasortransform/phasortransform.js");

// Select elements from GUI
const ptuFileBtn = document.getElementById("ptuSubmit");
const processPtuBtn = document.getElementById("processPtu");
const imageCanvas = document.getElementById("outputImg");
const phasorBtn = document.getElementById("makePhasor");
const calcHistBtn = document.getElementById("calcHist");
const colorBtn = document.getElementById("MapLifetimeToColor");

// Initializing variables
var fileDecoded; // JavaScript object; holds decoded ptu events and is appended with intensity image and phasor coordinates


// Listening for button clicks on the .ptu file button and sending request to main process via IPC to get the filepath, via channel "ptu-filepath"
ptuFileBtn.addEventListener("click", function (event) {
      ipc.send("ptu-filepath");
});



// Listening for filepath on "selectedptu" channel
let fp = "";
ipc.on("selectedptu", function (event, path) {
      if (fileDecoded) {
            fileDecoded = null; // Dereferencing when new file is loaded to free up memory
            console.info("Deleted old data.")
      }
      var channelSelected = document.getElementById("channelSelector").value;
      var binningFactor = document.getElementById("binningFactor").value;
      fp = path[0];
      fileDecoded = PTUReader.decodePTU(fp); // Decoding .ptu file
      fileDecoded.nanoPixelArr = nanoToPixel.attachNanotimes(fileDecoded, channelSelected, binningFactor)

      // Display filename to User
      document.getElementById("filename").innerHTML = fileDecoded.shortinfo.filename;
      document.getElementById("fileinfo").innerHTML = fileDecoded.shortinfo.fileinfo;
});


// Chose PTU file, decode it, calculate intensity image -> decoded ptu saved as "fileDecoded" in RAM
processPtuBtn.addEventListener("click", function (event) {
      if (fileDecoded) {
            var intensityMultiplicator = document.getElementById("intensityMultiplicator").value;
            fileDecoded.intensityArray = imgCalc.calculateIntensityImage(fileDecoded.nanoPixelArr);
            intImg.showImage(fileDecoded.intensityArray, imageCanvas, intensityMultiplicator);

            // Dereferencing raw data
            fileDecoded.markers = null;
            fileDecoded.nanotime = null;
            fileDecoded.macrotime = null;
      } else {
            alert("A .ptu file has to be loaded first.");
      };

});

// Calculate overall decay and show it for data selection
calcHistBtn.addEventListener("click", function () {
      if (fileDecoded) {
            var thresholdHist = document.getElementById("thresholdHist").value;
            var histShiftLeft = document.getElementById("histShiftLeft").value;
            var histShiftRight = document.getElementById("histShiftRight").value;
            var histOffset = document.getElementById("offsetHist").value;
            var binningFactorTemporal = document.getElementById("binningFactorTemporal").value;
            histCalc.showOverallDecay(fileDecoded, binningFactorTemporal, thresholdHist, histShiftLeft, histShiftRight, histOffset);
      } else {
            alert("Load a .ptu-file first!");
      }
});


// Calculate phasor transform 
phasorBtn.addEventListener("click", () => {
      if (fileDecoded == undefined) {
            alert("You need to load a .PTU first!")
      } else {
            if (fileDecoded.nanoPixelArr != undefined) {
                  fileDecoded.phasors = null;
            };
            // Calculating phasors

            var thresholdHist = document.getElementById("thresholdHist").value;
            var histShiftLeft = document.getElementById("histShiftLeft").value;
            var histShiftRight = document.getElementById("histShiftRight").value;
            var histOffset = document.getElementById("offsetHist").value;
            var binningFactorTemporal = document.getElementById("binningFactorTemporal").value;
            var frequencyMultiplicator = document.getElementById("frequencyMultiplicator").value;
            fileDecoded.phasors = phasorCalc.phasorTransform(fileDecoded, binningFactorTemporal, thresholdHist, histShiftLeft, histShiftRight, histOffset, frequencyMultiplicator);
            // let lifetimeFromPhasorAv = phasorCalc.calculateLifetime(fileDecoded.phasors);
            phasorCalc.showPhasor(fileDecoded, frequencyMultiplicator);
      };

});


// Colorize the image according to user-set lifetime range
colorBtn.addEventListener("click", function (event) {
      var donoronly = document.getElementById("donoronly").value;
      var fretpositive = document.getElementById("fretpositive").value;
      var frequencyMultiplicator = document.getElementById("frequencyMultiplicator").value;
      var intensityMultiplicator = document.getElementById("intensityMultiplicator").value;
      intImg.colorizeFromLifetimeRange(fileDecoded, frequencyMultiplicator, intensityMultiplicator, donoronly, fretpositive);
});