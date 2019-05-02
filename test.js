function makeSequence(start, stop, step) {
      var steps = Math.ceil((stop - start) / step);
      var arr = new Array(steps);
      var i = 0, value = start;
      for (i; i <= steps; i++) {
            arr[i] = (value + step * i);
      };
      return (arr);

};

function calcExponentialDecay(time, a, tau) {
      var length = time.length;
      var arr = new Array(length);
      var i;
      for (i = 0; i < length; i++) {
            arr[i] = a * Math.exp(-time[i] / tau);
      };

      return (arr);
};


var time = makeSequence(0, 25000, 14);
var exp = calcExponentialDecay(time, 1000, 2500);

var tmp = new Array(exp.length);
var sumNum = 0;
var i;

for (i = 0; i < exp.length - 1; i++) {
      sumNum += exp[i];
}

var gtemp = 0;
var angfreq = 2 * Math.PI * 80000000;

for (i = 0; i < exp.length - 1; i++) {
      tmp[i] = exp[i] * Math.cos(angfreq * exp[i]);
};

var sumDem = 0;

for (i = 0; i < exp.length - 1; i++) {
      sumDem += tmp[i];
};

console.log(sumDem);