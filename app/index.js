const fs = require("fs");

var test = [
      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      [10, 59, 84, 2, 4575, 474, 84, 4, 14, 2]
];

var path = "./test.csv";
var header = ["Lifetime", "Counts"];

var writeStream = fs.createWriteStream(path);

writeStream.write(header.toString() + "\n");

var tmp, i;
for (i = 0; i < test[0].length; i++) {
      tmp = [test[0][i], test[1][i]].toString();
      writeStream.write(tmp + "\n");
};


writeStream.close();