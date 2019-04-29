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
      ipc.send("showProgressbar"); // Show progressbar as long as we "synchronously" process the file
      fileDecoded = PTUReader.decodePTU(fp);
      ipc.send("setProgressbarCompleted");
});


// Chose PTU file, decode it, calculate intensity image -> decoded ptu saved as "fileDecoded" in RAM
processPtuBtn.addEventListener("click", function (event) {
      let intImageArr = imgCalc.calculateIntensityImage(fileDecoded);
      intImg.showImage(intImageArr, imageCanvas);
      var notif_finishedDecoding = new window.Notification("Finished Decoding PTU", {
            body: "Phasor FLIM has finished decoding your .ptu file."
      });

      fileDecoded.intImage = intImageArr; // Adding the intensity image data to fileDecoded
});


// Calculate phasor transform 
phasorBtn.addEventListener("click", function () {

      if (fileDecoded == undefined) {
            alert("You need to load a .PTU first!")
      } else {
            fileDecoded.nanoPixelArr = nanoToPixel.attachNanotimes(fileDecoded);
            fileDecoded.phasors = phasorCalc.phasorTransform(fileDecoded, 1);
      }

});