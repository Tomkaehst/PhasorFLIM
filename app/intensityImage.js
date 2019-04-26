/*
      Reconstructing the intensity image of the .ptu file decoded by PTUReader.js which outputs:
      - macrotime array: events on experiment timescale
      - nanotime array: events relative to last sync pulse
      - markers array: encodes event type (1, 2: photon in channel 1/2; 6: line start; 7: line stop; 63: overflow)
      - shortinfo: JavaScript Object with relevant information for image reconstruction from file header
      - fullinfo: Complete header from .ptu file
*/


var PTUReader = require("./PTUReader.js");

var testFile = PTUReader.decodePTU("./data/Convalaria_for_CC_6_1.ptu");

// Initializing 2D array for image reconstruction
/*
      Creating a matrix consisting of an array(pixel X), each in turn containing an array (pixel Y)
*/

var arr = new Array(testFile.shortinfo.pixelX);

for (var i = 0; i < arr.length; i++) {
      arr[i] = new Array(testFile.shortinfo.pixelY);
}

// Counting line start / stop markers and check if it matches info in shortinfo object

function checkLineMarkers(FLIMarr) {
      let counterStart = 0;
      let counterStop = 0;
      FLIMarr.markers.forEach(function (marker) {
            if (marker == 6) { counterStart++; }
            if (marker == 7) { counterStop++; }
      });

      if (counterStart != counterStop) {
            console.error("Number of line start and line stop markers do not match. Corrupted file?")
      }

      console.log(counterStart + " line start and " + counterStop + " line stop markers found.");
      console.log("Image dimensions: X = " + FLIMarr.shortinfo.pixelX + ", Y = " + FLIMarr.shortinfo.pixelY);
      console.log("FLIM Image with " + (counterStart / FLIMarr.shortinfo.pixelX) + "/" + (counterStop / FLIMarr.shortinfo.pixelX) + " scan repetitions");
};

checkLineMarkers(testFile);