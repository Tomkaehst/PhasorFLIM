module.exports = {
      showImage: function (arr, imgcanv, intensityMultiplicator) {
            var imgX = arr.length;
            var imgY = arr[0].length;
            var canv = imgcanv.getContext("2d");

            imgcanv.width = imgX;
            imgcanv.height = imgY;
            var imgData = canv.createImageData(imgX, imgY);

            var i, x, y;
            i = 0;

            for (x = 0; x < imgX; x++) {
                  for (y = 0; y < imgY; y++) {
                        imgData.data[i + 0] = 255;
                        imgData.data[i + 1] = 255;
                        imgData.data[i + 2] = 255;
                        imgData.data[i + 3] = arr[x][y] * intensityMultiplicator;
                        i += 4;

                  };
            };

            canv.putImageData(imgData, 0, 0);
            return (imgData);

      },

      /*
            This function is called from phasortransform.showPhasor() and is triggered by the event of data selection on the plotly by the user. The plot returns the selected data points which here are matched to the corresponding pixel on the image. The pixels in the intensity image are colorized respectively to allow for the visialization of FLIM data only using the phasor plot.

            colorizeFromPhasorSelection() acts on the intensityArray of the fileDecoded object!
      */
      colorizeFromPhasorSelection(decodedFile, indices) {
            let canv = document.getElementById("colorImg").getContext("2d");
            let imgData = decodedFile.intensityArray;
            let imgX = imgData.length;
            let imgY = imgData[0].length;
            let imgData_wColor = canv.createImageData(imgX, imgY);
            var intensityMultiplicator = document.getElementById("intensityMultiplicator").value;

            let colorSelector = document.getElementById("colorSelector").value - 1;
            let colorArr = [
                  [220, 20, 60],
                  [255, 255, 0],
                  [0, 255, 127]
            ];

            var i, x, y, index, indicesCounter;
            i = 0;
            index = 0;
            indicesCounter = 0;

            for (x = 0; x < imgX; x++) {
                  for (y = 0; y < imgY; y++) {
                        if (index == indices[indicesCounter]) {
                              imgData_wColor.data[i + 0] = colorArr[colorSelector][0];
                              imgData_wColor.data[i + 1] = colorArr[colorSelector][1];
                              imgData_wColor.data[i + 2] = colorArr[colorSelector][2];
                              indicesCounter++;
                        } else {
                              imgData_wColor.data[i + 0] = colorArr[colorSelector + 1][0];
                              imgData_wColor.data[i + 1] = colorArr[colorSelector + 1][1];
                              imgData_wColor.data[i + 2] = colorArr[colorSelector + 1][2];
                        };
                        imgData_wColor.data[i + 3] = imgData[x][y] * intensityMultiplicator + 50;
                        i += 4;
                        index++;
                  };
            };

            canv.putImageData(imgData_wColor, 0, 0);
            imgData_wColor = null;
      },

      colorizeFromLifetimeRange: function (decodedFile, frequencyMultiplicator, intensityMultiplicator, tauStart, tauEnd) {
            const colormap = require("colormap");
            let canv = document.getElementById("colorImg").getContext("2d");
            let imgData = decodedFile.intensityArray;
            let imgX = imgData.length;
            let imgY = imgData[0].length;
            let imgData_wColor = canv.createImageData(imgX, imgY + 20);

            var angularFrequency = 2 * Math.PI * decodedFile.shortinfo.syncRate * frequencyMultiplicator;
            var lifetimeRange = tauStart - tauEnd;
            var colors = new colormap({
                  colormap: "jet",
                  nshades: 100,
                  format: "rgba"
            })


            var i, x, y, index, lifetimeTemp, colorTemp;
            i = 0;

            for (x = 0; x < imgX; x++) {
                  for (y = 0; y < imgY; y++) {
                        if (decodedFile.phasors[x][y][1] != undefined || decodedFile.phasors[x][y][0] != undefined) {

                              lifetimeTemp = ((1 / angularFrequency) * (decodedFile.phasors[x][y][1] / decodedFile.phasors[x][y][0])) * 1E9;
                              index = Math.floor(((lifetimeTemp - tauEnd) / lifetimeRange) * 100);

                              if (index < 0) {
                                    colorTemp = colors[0];
                              } else if (index > colors.length - 1) {
                                    colorTemp = colors[colors.length - 1];
                              } else {
                                    colorTemp = colors[index];
                              }

                        } else {
                              colorTemp = [255, 255, 255];
                        };

                        imgData_wColor.data[i + 0] = colorTemp[0];
                        imgData_wColor.data[i + 1] = colorTemp[1];
                        imgData_wColor.data[i + 2] = colorTemp[2];
                        imgData_wColor.data[i + 3] = imgData[x][y] * intensityMultiplicator;
                        i += 4;
                  };
            };
            canv.putImageData(imgData_wColor, 0, 0);
            imgData_wColor = null;
      }
};