const fs = require("fs");

var tagTypes = {
      Empty8: 4294901768,
      Bool8: 8,
      Int8: 268435464,
      Color8: 301989896,
      Float8: 536870920,
      DateTime: 553648136,
      Float8Array: 537001983,
      AnsiString: 1073872895,
      WideString: 1073938431
};

// Not all record types are implemented here! We only have a HydraHarp2T3. To complement the missing record types, see https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos
var recordTypes = {
      HydraHarp2T3: 16843524
};


// Loading the .ptu file in ./data into the buffer
var filePath = "./Convalaria_for_CC_6_1.ptu"
console.info("Decoding " + filePath + "\n");
let data = fs.readFileSync(filePath);

// Check if file is a valid .ptu -> MAGIC = 'PQTTTR' and file version
var offset = 0;
var magic = data.slice(offset, offset + 6).toString("utf8");
offset += 8;
var version = data.slice(offset, offset + 6).toString();
offset += 8;

if (magic != "PQTTTR") {
      alert("Not a (valid) .ptu file!");
      throw "Not a (valid) .ptu file.";
};


// Decoding the header section
const tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
var offset_Header_End = data.indexOf(tag_HeaderEnd) + 48;

offset = offset_Header_End;

//let records = data.readUInt32LE(offset);

let records = [];

for (offset; offset <= 10000; offset += 4) {
      records.push(data.readUInt32LE(offset));
};

// Read the three bit fields
let channel = [];
let macro = [];
let nano = [];

records.forEach((record) => {
      channel.push((record >>> 25) & 2 ** 7 - 1);
      nano.push((record >>> 10) & 2 ** 15 - 1);
      macro.push(record & (2 ** 10 - 1));
});

// Correct macro times
let overflow_period = 1024;
let overflow_corr = 0;
let macro_corrected = [];

macro.forEach(function (time, index) {
      if (channel[index] == 127) {
            overflow_corr += overflow_period * macro[index];
      };
      macro_corrected.push((overflow_corr + time));
});

console.log(macro_corrected.slice(200, 300));