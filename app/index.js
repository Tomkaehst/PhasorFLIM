
function makeSequence(start, stop, step) {
      var steps = Math.ceil((stop - start) / step);
      var arr = new Array(steps);
      var i = 0, value = start;
      for (i; i <= steps; i++) {
            arr[i] = (value + step * i);
      };
      return (arr);

};

function calcExponentialDecay(time) {
      var length = time.length;
      var arr = new Array(length);
      var i;
      for (i = 0; i < length; i++) {
            arr[i] = Math.exp(-time[i]);
      };

      return (arr);
};


var test = makeSequence(0, 5, 0.75);
var exp = calcExponentialDecay(test);

console.log(test);
console.log(exp);