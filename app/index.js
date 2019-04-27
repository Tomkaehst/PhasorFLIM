
var PTUreader = require("./PTUReader.js");

var fp = "./data/EGFP-Cherry-Control_4_1.ptu";

var out = PTUreader.decodePTU(fp);

console.log(out.markers.slice(2500, 2900));



