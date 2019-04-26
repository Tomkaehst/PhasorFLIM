
var PTUreader = require("./PTUReader.js");

var fp = "./data/Convalaria_for_CC_6_1.ptu";

var out = PTUreader.decodePTU(fp);

console.log(out.markers.slice(2500, 2900));



