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

            // if (savePath != "") {
            //       var pngData = imgcanv.toDataURL(imgcanv);
            //       var downloadLink = document.createElement("a");
            //       downloadLink.textContent = "Save as PNG"
            //       downloadLink.href = pngData;
            //       downloadLink.download = "intensityImage.png";
            //       document.body.appendChild(downloadLink);
            //       console.log(downloadLink);
            // };

      },

      /*
            This function is called from phasortransform.showPhasor() and is triggered by the event of data selection on the plotly by the user. The plot returns the selected data points which here are matched to the corresponding pixel on the image. The pixels in the intensity image are colorized respectively to allow for the visialization of FLIM data only using the phasor plot.

            colorizeFromPhasorSelection() acts on the intensityArray of the fileDecoded object!
      */
      colorizeFromPhasorSelection(decodedFile, indices, color) {
            let canv = document.getElementById("colorImg").getContext("2d");
            let colorArr = [255, 0, 125];
            let imgData = decodedFile.intensityArray;
            let imgX = imgData.length;
            let imgY = imgData[0].length;
            let imgData_wColor = canv.createImageData(imgX, imgY);
            var intensityMultiplicator = document.getElementById("intensityMultiplicator").value;

            var i, x, y, index, indicesCounter;
            i = 0;
            index = 0;
            indicesCounter = 0;

            for (x = 0; x < imgX; x++) {
                  for (y = 0; y < imgY; y++) {
                        if (index == indices[indicesCounter]) {
                              imgData_wColor.data[i + 0] = 255;
                              imgData_wColor.data[i + 1] = 0;
                              imgData_wColor.data[i + 2] = 125;
                              indicesCounter++;
                        } else {
                              imgData_wColor.data[i + 0] = 255;
                              imgData_wColor.data[i + 1] = 255;
                              imgData_wColor.data[i + 2] = 255;
                        };
                        imgData_wColor.data[i + 3] = imgData[x][y] * intensityMultiplicator;
                        i += 4;
                        index++;
                  };
            };

            canv.putImageData(imgData_wColor, 0, 0);
      }
};