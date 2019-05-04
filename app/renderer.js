// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.
const ipc = require("electron").ipcRenderer;

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
const overallDecayBtn = document.getElementById("showOverallDecay");


// Initializing variables
let fileDecoded; // JavaScript object; holds decoded ptu events and is appended with intensity image and phasor coordinates


// Listening for button clicks on the .ptu file button and sending request to main process via IPC to get the filepath, via channel "ptu-filepath"
ptuFileBtn.addEventListener("click", function (event) {
      ipc.send("ptu-filepath");
});



// Listening for filepath on "selectedptu" channel
let fp = "";
ipc.on("selectedptu", function (event, path) {
      if (fileDecoded) {
            fileDecoded = null; // Dereferencing when new file is loaded to free up memory
      }
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
            //fileDecoded.intImage = intImageArr; // Adding the intensity image data to fileDecoded
      } else {
            alert("A .ptu file has to be loaded first.");
      };

});


// Calculate phasor transform 
phasorBtn.addEventListener("click", function () {
      if (fileDecoded == undefined) {
            alert("You need to load a .PTU first!")
      } else {
            if (fileDecoded.nanoPixelArr) {
                  fileDecoded.nanoPixelArr = null;
                  fileDecoded.phasors = null;
            };
            // Calculating phasors
            var channelSelected = document.getElementById("channelSelector").value;
            var binningFactorPhasorSpatial = document.getElementById("binningFactorPhasorSpatial").value;
            var binningFactorPhasorTemporal = document.getElementById("binningFactorPhasorTemporal").value;
            var thresholdPhasor = document.getElementById("thresholdPhasor").value;
            var frequencyMultiplicator = document.getElementById("frequencyMultiplicator").value;
            fileDecoded.nanoPixelArr = nanoToPixel.attachNanotimes(fileDecoded, channelSelected, binningFactorPhasorSpatial);
            fileDecoded.phasors = phasorCalc.phasorTransform(fileDecoded, binningFactorPhasorTemporal, thresholdPhasor, frequencyMultiplicator);
            phasorCalc.showPhasor(fileDecoded.phasors);
      };

});

overallDecayBtn.addEventListener("click", function () {
      if (fileDecoded.nanoPixelArr) {
            var binningFactorPhasorTemporal = document.getElementById("binningFactorPhasorTemporal").value;
            var thresholdPhasor = document.getElementById("thresholdPhasor").value;
            phasorCalc.showOverallDecay(fileDecoded, binningFactorPhasorTemporal, thresholdPhasor);
      } else {
            alert("Calculate the phasor first! (Only temporarily...)");
      }
})