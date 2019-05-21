module.exports = {
      exportIntensityImage: function (imageCanvas) {
            var url = imageCanvas.toDataURL("image/jpeg", 1);
            var base64img = url.replace(/^data:image\/jpeg;base64,/, "");
            return (base64img);
      },

      exportLifetimeImage: function (imageCanvas) {
            var url = imageCanvas.toDataURL("image/jpeg", 1);
            var base64img = url.replace(/^data:image\/jpeg;base64,/, "");
            return (base64img);
      }
}

