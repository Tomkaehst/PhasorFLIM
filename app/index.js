

var fp = "./data/Convalaria_for_CC_6_1.ptu";

const imgCalc = require("./intensityImage.js");

let testArr = imgCalc.calculateIntensityImage(fp);

console.log(testArr);