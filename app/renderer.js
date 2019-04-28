// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// All of the Node.js APIs are available in this process.

const ipc = require("electron").ipcRenderer;

// Loading script for calculation of intensity image; requires PTUReader.js; --> provide filepath to imgCalc.calculateIntensityImage()
const imgCalc = require("./intensityImage.js");

// Select elements from GUI
const ptuFileBtn = document.getElementById("ptuSubmit");
const processPtu = document.getElementById("processPtu");
const imageCanvas = document.getElementById("outputImg").getContext("2d");


// Listening for button clicks on the .ptu file button and sending request to main process via IPC to get the filepath, via channel "ptu-filepath"
ptuFileBtn.addEventListener("click", function (event) {
      ipc.send("ptu-filepath");
      console.log("Send request for .ptu filepath");
});



// Listening for filepath on "selectedptu" channel
let fp = "";

ipc.on("selectedptu", function (event, path) {
      fp = path[0];
});


// Checking if user wants to process the file
processPtu.addEventListener("click", function (event) {
      if (fp == "") {
            alert("Select a .ptu file!");
      } else {
            let imgArr = imgCalc.calculateIntensityImage(fp);
            showImage(imgArr, imageCanvas);
      }
});

function showImage(arr, canv) {
      var imgX = arr.length - 1;
      var imgY = arr[0].length - 1;

      var imgData = canv.createImageData(imgX, imgY);

      var i, x, y;
      i = 0;

      for (x = 0; x <= imgX; x++) {
            for (y = 0; y <= imgY; y++) {
                  imgData.data[i + 0] = 255;
                  imgData.data[i + 1] = 255;
                  imgData.data[i + 2] = 255;
                  imgData.data[i + 3] = arr[x][y] * 20;
                  i += 4;
            };
      };

      canv.putImageData(imgData, 10, 10);

};