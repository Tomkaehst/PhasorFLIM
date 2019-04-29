module.exports = {
      showImage: function (arr, imgcanv) {
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
                        imgData.data[i + 3] = arr[x][y] * 5;
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

      }
};