module.exports = {
      attachNanotimes: function (decodedFile) {

            // Passing JavaScript OBJECT as function argument passes reference to that object!
            let arr = decodedFile;

            // Initializing 3D array ([x][y][n]) to attach n nanotimes to each pixel by appending (histogram will be calculated from that "on the fly" to save RAM)
            var j;
            var i;

            let imgArr = new Array(arr.shortinfo.pixelX); // Assuming a square image!

            for (i = 0; i < imgArr.length; i++) {
                  imgArr[i] = new Array(arr.shortinfo.pixelY);
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
            let pixelID = 0;

            while (lastLine == false) {

                  tmpMarker = arr.markers[eventCounter];

                  if (tmpMarker == 6) { // event is line start
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

                        if (tmpMarker == 0 || tmpMarker == 1) { // We do not distinguish between channel event FOR NOW!
                              tmpEvents.push(tmpMacro);
                              tmpNano.push(tmpNanotime);
                        } else if (tmpMarker == 7) {
                              lineActive = false;
                              lineStop = tmpMacro;
                              pixelTime = (lineStop - lineStart) / arr.shortinfo.pixelX;

                              // assign the photons from a lineActive period to the corresponding pixels of arr[lineCounter][pixel]
                              for (var i = 0; i <= tmpEvents.length - 1; i++) {
                                    diff = tmpEvents[i] - lineStart;
                                    pixelID = Math.floor(diff / pixelTime);

                                    if (pixelID < 0 || pixelID > arr.shortinfo.pixelX - 1) {
                                          console.error("Pixel out of range! Line: " + lineCounter + ", Pixel: " + pixelID + ", Frame: " + frameCounter + "\n Assigned out-of-range pixel to nearest edge.");
                                          if (pixelID < 0) pixelID = 0;
                                          if (pixelID > arr.shortinfo.pixelX - 1) pixelID = arr.shortinfo.pixelX - 1;
                                    }
                                    imgArr[lineCounter][pixelID].push(tmpNano[i]);
                              };
                              lineCounter++;
                              tmpEvents = [];
                              tmpNano = [];
                              continue;
                        };

                        eventCounter++;

                  };



                  // Check if all lines in one frame have been evaluated
                  if (lineCounter > (arr.shortinfo.pixelX - 1)) {
                        frameCounter++;
                        lineCounter = 0;
                  };

                  // terminate while loop when last frame is detected
                  if (frameCounter >= framesInFile) {
                        lastLine = true;
                        console.log("Processed " + arr.shortinfo.numRec + " events from " + frameCounter + " frame scannings.\n")
                        //break;
                  };


                  eventCounter++;
            };

            return (imgArr);
      }
};