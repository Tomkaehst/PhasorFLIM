
const fs = require("fs")
const path = require("path")


// Adapted from https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos


var tagTypes = {
      Empty8: 0xFFFF0008,
      Bool8: 0x00000008,
      Int8: 0x10000008,
      Color8: 0x12000008,
      Float8: 0x20000008,
      DateTime: 0x21000008,
      Float8Array: 0x2001FFFF,
      AnsiString: 0x4001FFFF,
      WideString: 0x4002FFFF
}

// Not all record types are implemented here! We only have a HydraHarp2T3. To complement the missing record types, see https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos
var recordTypes = {
      HydraHarp2T3: 0x01010304
}

//console.log(tagTypes.Empty8.toString());


// Loading the .ptu file in ./data into the buffer
//filePath = "./data/lol.txt"
filePath = "./data/Convalaria_for_CC_6_1.ptu"

let data = fs.readFileSync(filePath); // Need to switch to asynchronous reading for larger files!


// Check if file is a valid .ptu -> MAGIC = 'PQTTTR' and file version
var offset = 0;
var magic = data.slice(offset, offset + 6).toString("utf8");
offset += 8;
var version = data.slice(offset, offset + 6).toString();
offset += 8;

if (magic != "PQTTTR") {
      throw "Not a valid .ptu file."
}


// Decoding the header section
const tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
let reachedHeaderEnd = false;

var HeaderContents = [ // add header info to this array via .push({tag: content})
      { FileMagic: magic },
      { FileVersion: version }
];


/*
      Explanation: Header Decoding .ptu files
      ----------------------------------------
      
*/

while (reachedHeaderEnd == false) {
      var tag_data = data.slice(offset, offset + 48);
      offset += 48;
      var tagId = tag_data.slice(0, 32).toString().replace(/\0/g, ""); // .replace() removes zero padding using regex!
      var tagIdx = tag_data.slice(32, 36).readInt32LE();
      var typeCode = tag_data.slice(36, 40).readUInt32LE();
      var tagVal = tag_data.slice(40, 48);


      if (typeCode == tagTypes.Empty8) {
            if (tagId == tag_HeaderEnd) {
                  reachedHeaderEnd = true;
            } else {
                  HeaderContents.push({ [tagId]: tagVal.readUInt8() });
            }
      }
      else if (typeCode == tagTypes.Bool8) {
            HeaderContents.push({ [tagId]: tagVal.readUInt8() });
      }
      else if (typeCode == tagTypes.Int8) {
            HeaderContents.push({ [tagId]: tagVal.readUInt8() });
      }
      else if (typeCode == tagTypes.Color8) {
            HeaderContents.push({ [tagId]: tagVal.readInt8() });
      }
      else if (typeCode == tagTypes.Float8) {
            var entry = tagVal
            HeaderContents.push({ [tagId]: tagVal.readDoubleLE() });
      }
      else if (typeCode == tagTypes.DateTime) {
            HeaderContents.push({ [tagId]: tagVal.readInt32LE() });
      }
      else if (typeCode == tagTypes.Float8Array) {
            if (tagVal.readUInt32LE() % 8 == 0) {
                  var entry = data.slice(offset, offset + tagVal.readUInt32LE());
                  offset += tagVal;
            } else {
                  throw "Error in Float8Array decoding in .ptu header."
            }
            HeaderContents.push({ [tagId]: entry });
      }
      else if (typeCode == tagTypes.AnsiString) {
            if (tagVal.readUInt32LE() % 8 == 0) {
                  var entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString().replace(/\0/g, "");
                  offset += tagVal.readUInt32LE();
            } else {
                  throw "Error in AnsiString decoding in .ptu header."
            }
            HeaderContents.push({ [tagId]: entry });
      }
      else if (typeCode == tagTypes.WideString) {
            if (tagVal.readUInt32LE() % 8 == 0) {
                  var entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('utf16').replace(/\0/g, "");
                  offset += tagVal.readUInt32LE();
            } else {
                  throw "Error in WideString decoding in .ptu header."
            }
            HeaderContents.push({ [tagId]: entry });
      }
      else {
            console.log("Error occured during header decoding.")
      }
}


console.log(HeaderContents);


console.log(data.slice(offset, offset + 48).toString());