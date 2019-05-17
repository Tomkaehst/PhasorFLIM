const colormap = require("colormap");

var colors = new colormap({
      colormap: "jet",
      nshades: 100,
      format: "rgba"
})

let arr = new Array(10);
var x, y;
let value = 0;

for (x = 0; x < arr.length; x++) {
      arr[x] = new Array(10);
      for (y = 0; y < arr[0].length; y++) {
            arr[x][y] = colors[value];
            value += 1;
      };
};

var test = colors[20];

console.log(test[0]);