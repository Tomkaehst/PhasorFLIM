/*
      Reconstructing the intensity image of the .ptu file decoded by PTUReader.js which outputs:
      - macrotime array: events on experiment timescale
      - nanotime array: events relative to last sync pulse
      - markers array: encodes event type (1, 2: photon in channel 1/2; 6: line start; 7: line stop; 63: overflow)
      - shortinfo: JavaScript Object with relevant information for image reconstruction from file header
      - fullinfo: Complete header from .ptu file
*/


module.exports = {
      calculateIntensityImage: function (filePath) {


            // Not optimal, but for now I put two helper functions inside the def of calculateIntensityImage because of "legacy" reasons.
            function averageLineTime(arr) {
                  var startTimes = [];
                  var stopTimes = [];
                  var recordLength = arr.macrotime.length - 1;

                  for (var i = 0; i <= recordLength; i++) {
                        if (arr.markers[i] == 6) {
                              startTimes.push(arr.macrotime[i]);
                        } else if (arr.markers[i] == 7) {
                              stopTimes.push(arr.macrotime[i])
                        }
                  };

                  var lines = startTimes.length - 1;
                  var sum = 0;

                  for (var i = 0; i <= lines; i++) {
                        var diff = (stopTimes[i] - startTimes[i]);
                        sum += diff;
                  };

                  sum /= lines;

                  return (sum);
            };

            function checkLineMarkers(FLIMarr) {
                  let counterStart = 0;
                  let counterStop = 0;
                  FLIMarr.markers.forEach(function (marker) {
                        if (marker == 6) { counterStart++; }
                        if (marker == 7) { counterStop++; }
                  });

                  if (counterStart != counterStop) {
                        console.error("Number of line start and line stop markers do not match. Corrupted file?")
                  };

                  console.log(counterStart + " line start and " + counterStop + " line stop markers found.");
                  console.log("Image dimensions: X = " + FLIMarr.shortinfo.pixelX + ", Y = " + FLIMarr.shortinfo.pixelY + "\n");
                  console.log("FLIM Image with " + (counterStart / FLIMarr.shortinfo.pixelX) + "/" + (counterStop / FLIMarr.shortinfo.pixelX) + " scan repetitions.\n");
                  console.log(FLIMarr.shortinfo.numRec + " events in decoded .ptu file.\n")

                  return (counterStart);
            };



            const PTUReader = require("./PTUReader");

            //var filePath = "./data/20180907_EGFP_RAD51_Cherry_RAD52_1_3.ptu";
            let testFile = PTUReader.decodePTU(filePath);



            // Counting line start / stop markers and check if it matches info in shortinfo object
            testFile.shortinfo.lines = checkLineMarkers(testFile);

            testFile.shortinfo["avgLineTime"] = averageLineTime(testFile);

            /* Calculating the intensity image */

            // Initializing 2D array for image reconstruction
            var arr = new Array(testFile.shortinfo.pixelX).fill(0);

            for (var i = 0; i < arr.length; i++) {
                  arr[i] = new Array(testFile.shortinfo.pixelY).fill(0);
            }



            // Initializing counter and neccessary variables
            let eventCounter = 260;
            let lineCounter = 0; // Tracks current line 
            let frameCounter = 0; // counts frames, incremented when lineCounter > pixelX
            let framesInFile = testFile.shortinfo.lines / testFile.shortinfo.pixelX; // number of frames: lines / pixels in dimension; assumes square image
            let totalLines = testFile.shortinfo.lines // number of lines in the file
            let pixelTime = testFile.shortinfo.avgLineTime / testFile.shortinfo.pixelX; // assuming that the image is a square
            let lineTime = testFile.shortinfo.avgLineTime; // Average time duration of one scanning line
            let lineStart = 0; // absolute experiment time of the line start marker
            let lastLine = false; // set to true, when lineCounter >= totalLines, i.e. no more data
            let lineActive = false; // true when a line start marker (6) was detected; false if line stop marker (7) was detected;

            // tmp variables
            let tmpEvents = []; // temp storage for 
            let tmpMarker = 0;
            let tmpMacro = 0;
            let diff = 0; // temp storage for difference of macrotime(n) and the lineStart time for pixel assignment in a line
            let pixelID = 0;

            while (lastLine == false) {

                  tmpMarker = testFile.markers[eventCounter];
                  if (tmpMarker == 6) { // event is line start ?
                        lineActive = true;
                        lineStart = testFile.macrotime[eventCounter]; // Saving the time when the line start occured
                        eventCounter++;
                        continue; // skip the rest, because the event was a line marker
                  };


                  // saving photon events during lineActive in tmpEvents (only macrotimes!)
                  while (lineActive == true) {
                        tmpMarker = testFile.markers[eventCounter];
                        tmpMacro = testFile.macrotime[eventCounter];
                        if (tmpMarker == 1) { // only channel 1 for now
                              tmpEvents.push(tmpMacro);
                        } else if (tmpMarker == 7) {
                              lineActive = false;
                              lineCounter++;

                              // assign the photons from a lineActive period to the corresponding pixels of arr[lineCounter][pixel]
                              for (var i = 0; i <= tmpEvents.length - 1; i++) {
                                    diff = tmpEvents[i] - lineStart;
                                    pixelID = Math.round(diff / pixelTime);

                                    if (pixelID < 0 || pixelID > testFile.shortinfo.pixelX) {
                                          throw "Pixel out of range!";
                                          break;
                                    } else {
                                          arr[lineCounter][pixelID]++;
                                    }
                              };

                              tmpEvents = [];
                        };

                        eventCounter++;
                  };



                  // Check if all lines in one frame have been evaluated
                  if (lineCounter >= (testFile.shortinfo.pixelX - 1)) {
                        frameCounter++;
                        lineCounter = 0;
                  };

                  // terminate while loop when last frame is detected
                  if (frameCounter >= framesInFile) {
                        lastLine = true;
                        console.log("Finished calculating intensity image from " + filePath + "\n");
                        console.log("Processed " + testFile.shortinfo.numRec + " events from " + frameCounter + " frame scannings.\n")
                        break;
                  };


                  eventCounter++;
            };

            return (arr);

      }
};


