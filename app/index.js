const mathjs = require("mathjs");

// Can be replaced by mathjs.range(start, stop, step);
// function makeSequence(start, stop, step) {
//       var steps = Math.ceil((stop - start) / step);
//       var arr = new Array(steps);
//       var i = 0, value = start;
//       for (i; i <= steps; i++) {
//             arr[i] = (value + step * i);
//       };
//       return (arr);

// };

function calcExponentialDecay(time, a, tau) {
      var length = time.size()[0];
      var arr = new Array(length);
      var i;
      for (i = 0; i < length; i++) {
            arr[i] = a * Math.exp(-time.data[i] / tau);
      };

      return (arr);
};


let time = mathjs.range(0, 5E-8, 1.6E-11);

let exp = time.map(function (value, index, matrix) {
      return (mathjs.multiply(1000, mathjs.exp(-value / 2.5E-9)));
});



let harmonic = 1;
let freq0 = 80e6;
let freq = harmonic * freq0;
let angFreq = 2 * Math.PI * freq;
//let deltaT = 16E-12;
//let timebins = mathjs.round(1 / (freq0 * deltaT) * harmonic);

let g_innerMult = mathjs.multiply(time, angFreq);
let g_cos = mathjs.cos(g_innerMult);
let g_outerMult = mathjs.dotMultiply(g_cos, exp);
let g_sum = mathjs.sum(g_outerMult);
let exp_sum = mathjs.sum(exp);

console.log("Unnormalized: " + g_sum + " , Sum: " + exp_sum + "\n Divided: " + g_sum / exp_sum);