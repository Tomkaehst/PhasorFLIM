
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


var test = makeSequence(0, 50000, 50);
var exp = calcExponentialDecay(test, 1000, 2500);

calcPhasor(exp, test, 80e06);


function calcPhasor(decay, timeaxis, repFrequency) {
      let length = decay.length;
      let time = timeaxis;
      let angFrequency = 2 * Math.PI * repFrequency;
      let i, j;

      let sumDenominator = 0;
      let sumNumeratorG = 0;
      let sumNumeratorS = 0;
      let tmp = 0;

      for (i = 0; i < length - 1; i++) {
            sumDenominator += decay[i];
      };

      for (i = 0; i < length; i++) {
            //for (j = 0; j < length; j++) {
            tmp += decay[i] * Math.cos(time[i] * angFrequency);
            //};
            //sumNumeratorG += tmp;
            //tmp = 0;
      };

      // var g = sumNumeratorG / sumDenominator;
      // var s = sumNumeratorS / sumDenominator;
      console.log(sumNumeratorG / sumDenominator);
};