module.exports = {
      attachNanotimes: function (decodedFile, channel, binning) {

            const { ipcRenderer } = require("electron");

            // Passing JavaScript OBJECT as function argument passes reference to that object!
            let arr = decodedFile;
            let binningFactor = 2 ** binning;

            let pixelX = arr.shortinfo.pixelX / binningFactor;
            let pixelY = arr.shortinfo.pixelY / binningFactor;

            // Initializing 3D array ([x][y][n]) to attach n nanotimes to each pixel by appending (histogram will be calculated from that "on the fly" to save RAM)
            let i, j;

            let imgArr = new Array(pixelX); // Assuming a square image!
            for (i = 0; i < imgArr.length; i++) {
                  imgArr[i] = new Array(pixelY);
                  for (j = 0; j < imgArr[i].length; j++) {
                        imgArr[i][j] = new Array();
                  };
            };

            // Initializing counter and neccessary variables
            let eventCounter = 0;
            let lineCounter = 0; // Tracks current line 
            let frameCounter = 0; // counts frames, incremented when lineCounter > pixelX
            let framesInFile = arr.shortinfo.lines / arr.shortinfo.pixelX; // number of frames: lines / pixels in dimension; assumes square image
            let pixelTime = 0 // assuming that the image is a square; will be calculated when lineStart and lineStop were detected
            let lineStart = 0; // absolute experiment time of the line start marker
            let lineStop = 0;
            let lastLine = false; // set to true, when lineCounter >= totalLines, i.e. no more data
            let lineActive = false; // true when a line start marker (6) was detected; false if line stop marker (7) was detected;

            // tmp variables
            let tmpEvents = []; // temp storage for 
            let tmpNano = [];
            let tmpMarker = 0;
            let tmpMacro = 0;
            let tmpNanotime = 0;
            let diff = 0; // temp storage for difference of macrotime(n) and the lineStart time for pixel assignment in a line
            let pixelID_X = 0; // counter used to populate image array and accounting for binning factor
            let pixelID_Y = 0;

            while (lastLine == false) {

                  tmpMarker = arr.markers[eventCounter];

                  if (tmpMarker == 65) { // event is line start
                        lineActive = true;
                        lineStart = arr.macrotime[eventCounter]; // Saving the time when the line start occured
                        eventCounter++;
                        continue; // skip the rest, because the event was a line marker
                  };


                  // saving photon events during lineActive in tmpEvents in this inner loop to (hopefully) save some computation time
                  while (lineActive == true) {

                        tmpMarker = arr.markers[eventCounter];
                        tmpMacro = arr.macrotime[eventCounter];
                        tmpNanotime = arr.nanotime[eventCounter];

                        if (tmpMarker == channel) {
                              tmpEvents.push(tmpMacro);
                              tmpNano.push(tmpNanotime);
                        } else if (tmpMarker == 66) {
                              lineActive = false;
                              lineStop = tmpMacro;
                              pixelTime = (lineStop - lineStart) / pixelY;

                              // assign the photons from a lineActive period to the corresponding pixels of arr[lineCounter][pixel]
                              let i;
                              for (i = 0; i < tmpEvents.length - 1; i++) {
                                    diff = tmpEvents[i] - lineStart;
                                    pixelID_Y = Math.floor(diff / pixelTime);

                                    if (pixelID_Y < 0 || pixelID_Y > pixelY - 1) {
                                          console.error("Pixel out of range! Line: " + lineCounter + ", Pixel: " + pixelID_Y + ", Frame: " + frameCounter + "\n Assigned out-of-range pixel to nearest edge.");
                                          if (pixelID_Y < 0) pixelID_Y = 0;
                                          if (pixelID_Y > pixelX - 1) pixelID_Y = pixelX - 1;
                                    };
                                    imgArr[Math.floor(pixelID_X)][pixelID_Y].push(tmpNano[i]);
                              };

                              pixelID_X += 1 / binningFactor;
                              lineCounter++;
                              tmpEvents = [];
                              tmpNano = [];
                        };

                        eventCounter++;

                  };

                  // Check if all lines in one frame have been evaluated
                  if (lineCounter > (arr.shortinfo.pixelX - 1)) {
                        frameCounter++;
                        pixelID_X = 0;
                        lineCounter = 0;
                  };

                  // terminate while loop when last frame is detected
                  if (frameCounter >= framesInFile) {
                        lastLine = true;
                        console.log("Processed " + arr.shortinfo.numRec + " events from " + frameCounter + " frame scannings.\n")
                        break;
                  };


                  // Showing Progress to User
                  if (eventCounter % 25000 == 0) {
                        ipc.send("update-progressbar", ["Sorting photons ...", Math.round((eventCounter / arr.shortinfo.numRec) * 100)]);
                  };

                  eventCounter++;
            };

            // Stop showing progress bar
            ipc.send("end-progressbar");

            return (imgArr);
      }
};