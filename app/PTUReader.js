
const fs = require("fs")
const path = require("path")
const bitwise = require("bitwise");

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
      throw "Not a (valid) .ptu file."
}


// Decoding the header section
const tag_HeaderEnd = "Header_End"; // Last Entry of the Header; terminates reading loop
var offset_Header_End = data.indexOf("Header_End") + 48; // Used later to check whether the number of bytes without the header divived by 4 (because one record has 4 bytes) is equal to the numRec in the file header
let reachedHeaderEnd = false;

var HeaderContents = [ // add header info to this array via .push({[tagname]: content})
      { FileMagic: magic },
      { FileVersion: version }
];


/* Header Decoding .ptu files */

while (reachedHeaderEnd == false) {

      var tag_data = data.slice(offset, offset + 48);
      offset += 48;
      var tagId = tag_data.slice(0, 32).toString().replace(/\0/g, ""); // .replace() removes zero padding using regex!
      //var tagIdx = tag_data.slice(32, 36).readInt32LE(); // What's the point of that?
      var typeCode = tag_data.slice(36, 40).readUInt32LE();
      var tagVal = tag_data.slice(40, 48);


      if (typeCode == tagTypes.Empty8) {
            if (tagId == tag_HeaderEnd) {
                  reachedHeaderEnd = true;
                  offset -= 16; // Byte offset needs to be right at the end of the Header_End tag! (I think...)
            } else {
                  HeaderContents.push({ [tagId]: tagVal.readUInt8() });
            }
      }
      else if (typeCode == tagTypes.Bool8) {
            var entry = tagVal.readInt8 > 0 ? true : false;
            HeaderContents.push({ [tagId]: entry });
      }
      else if (typeCode == tagTypes.Int8) {
            HeaderContents.push({ [tagId]: tagVal.readInt32LE() });
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
                  offset += tagVal.readUInt32LE();
            } else {
                  throw "Error in Float8Array decoding in .ptu header."
            }
            HeaderContents.push({ [tagId]: entry });
      }
      else if (typeCode == tagTypes.AnsiString) {
            if (tagVal.readUInt32LE() % 8 == 0) {
                  var entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('latin1').replace(/\0/g, "");
                  offset += tagVal.readUInt32LE();
            } else {
                  throw "Error in AnsiString decoding in .ptu header."
            }
            HeaderContents.push({ [tagId]: entry });
      }
      else if (typeCode == tagTypes.WideString) {
            if (tagVal.readUInt32LE() % 8 == 0) {
                  var entry = data.slice(offset, offset + tagVal.readUInt32LE()).toString('latin1').replace(/\0/g, "");
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

// Grabbing relevant infos out of header for record reading

var FLIMInfo = { // Quite messed up -> think about that!
      globRes: HeaderContents[88].MeasDesc_GlobalResolution,
      measRes: HeaderContents[57].MeasDesc_Resolution,
      baseRes: HeaderContents[55].HW_BaseResolution,
      binFactor: HeaderContents[56].MeasDesc_BinningFactor,
      pixelRes: HeaderContents[26].ImgHdr_PixResol,
      pixelX: HeaderContents[24].ImgHdr_PixX,
      pixelY: HeaderContents[25].ImgHdr_PixY,
      numRec: HeaderContents[89].TTResult_NumberOfRecords,
      filename: HeaderContents[19].$Filename,
      bitsPerRecord: HeaderContents[93].TTResultFormat_BitsPerRecord,
      recType: HeaderContents[92].TTResultFormat_TTTRRecType
}

// Decoding the TTTR records in the file
/*A record is 4 byte = 32 bit long and, in the case of HydraHarp2T3 data, contains the following components:
 - special: 1 bit, if clear: regular record, if >= 1 its a special record: overflow or external marker
 - channel: 6 bits, either encodes channel ID of the photon event, or, if special is set, encodes which special case occured: if 111111 ( = 63), an overflow occured, 1 to 15 are (external) markers, such as line / frame start / stop (see header file)
 - dtime: 15 bits
 - nsync: 10 bits

 To recover the global arival time of a photon or marker in seconds, count overflows until the current position and multiply with overflow period (1024 for HydraHarp2T3). Then add nsync and multiply with MeasDesc_GlobalResolution (for T3, slightly different for T2!)
*/


// Checking the record type; currently only HydraHarp 2 T3 is implemented!
if (FLIMInfo.recType != recordTypes.HydraHarp2T3) {
      throw "TTTR records of your .ptu not implemented yet!"
}


// Checking if remaining bytes in data (without header) matched FLIMInfo.numRec

if (FLIMInfo.numRec != (data.byteLength - offset_Header_End) / 4) {
      throw "Number of records specified in header does not match number of remaining bytes in currently accessed file. Check file validity."
}

// Reading the records from the file into three arrays! (for now)
let macrotime = new Array(FLIMInfo.numRec);

let temp = data.slice(offset + 20, offset + 24);

var special = temp.slice(0, 1);
var channel = temp.slice(1, 7);
var dtime = temp.slice(7, 22);
var nsync = temp.slice(22, 32);

var test = bitwise.buffer.read(temp);
