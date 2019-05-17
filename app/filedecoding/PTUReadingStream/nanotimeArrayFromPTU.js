
const fs = require("fs");
const bitwise = require("bitwise");
const readHeader = require("./readPTUHeader.js");


// // Not all record types are implemented here! We only have a HydraHarp2T3. To complement the missing record types, see https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos
var recordTypes = {
      HydraHarp2T3: 16843524
};

// Reading file and decoding header
var filePath = "./Convalaria_for_CC_6_1.ptu";
console.info("Decoding " + filePath + "\n");

let test = readHeader.readHeader(filePath, readHeader.logHeader);









// dataStreamHeader
//       .on("data", (chunk) => {
//             console.log("Starting header reading stream ... \n");
//             headerOffset = chunk.indexOf("Header_End") + 48;
//             console.log(headerOffset);

//             if (headerOffset != -1) {
//                   if (readHeader.checkFileValidity(chunk.slice(0, 16)) != true) {
//                         dataStreamHeader.close();
//                         throw "Not a valid .ptu file!"
//                   } else {
//                         header = readHeader.readHeader(chunk.slice(16, headerOffset + 48));
//                         dataStreamHeader.close();
//                   }
//             };
//       })
//       .on("error", (err) => {
//             throw err;
//       })
//       .on("close", () => {
//             console.log("\nClosing header reading stream ...\n")
//       })


// // Check if file is a valid .ptu -> MAGIC = 'PQTTTR' and file version
// if (readHeader.checkFileValidity(data.slice(0, 16)) != true) {
//       throw "Not a valid .ptu file!"
// };

// // Decoding the header section
// let headerOffset = data.indexOf("Header_End") + 48;
// let FLIMInfo = readHeader.readHeader(data.slice(16, headerOffset));

// // Checking the record type; CURRENTLY ONLY HYDRAHARP2 T3 RECORDS ARE IMPLEMENTED!
// if (FLIMInfo.recType != recordTypes.HydraHarp2T3) {
//       throw "TTTR records of your .ptu not implemented yet!";
// }


// // Checking if remaining bytes in data (without header) matched FLIMInfo.numRec
// if (FLIMInfo.numRec != (data.byteLength - offset_Header_End) / 4) {
//       throw "Number of records specified in header does not match number of remaining bytes in currently accessed file. Check file validity.";
// }
// else {
//       console.log("Processing " + FLIMInfo.numRec + " records from " + filePath);
// }




// // Reading the records from the file into three arrays! (for now)
// let macrotime = new Array(FLIMInfo.numRec);
// let nanotime = new Array(FLIMInfo.numRec);
// let markers = new Array(FLIMInfo.numRec);
// const overflow_period = 1024;
// let overflowCorr = 0;
// let truensync = 0;
// let macroMultFactor = FLIMInfo.globRes // Multiply with truensync to get real experiment time in seconds
// let nanoMultFactor = FLIMInfo.measRes * 1e9;
// const bytesToFileEnd = data.byteLength - 4;
// let i = 0; // Counts

// // need to add 3 for some reason; bytes and bits seem to be out of order after the header; not much valuable photon data at the beginning of the file anyway; I hope this is not different for other files
// offset += 0;

// while (offset <= bytesToFileEnd) {
//       let recordBytes = data.slice(offset, offset + 4).reverse(); // Endianess change here; buffer has to be reversed! Took me 5 hours to find out!!!
//       let recordBits = bitwise.buffer.read(recordBytes);

//       let special = parseInt(recordBits.slice(0, 1), 2);
//       let channel = parseInt(recordBits.slice(1, 7).join(""), 2);
//       let dtime = parseInt(recordBits.slice(7, 22).join(""), 2);
//       let nsync = parseInt(recordBits.slice(22, 33).join(""), 2);
//       //let channel = parseInt(recordBits.slice(1, 7).toString().replace(/\,/g, ""), 2);

//       if (special == 1) {
//             if (channel == 63) {
//                   overflowCorr += (overflow_period * nsync);
//             }
//             else if (channel >= 1 & channel <= 15) {
//                   truensync = overflowCorr + nsync;
//                   // line start = 1 (from channel) + 5 -> 6; line stop = 2 (from channel) + 5 = 7; otherwise photon events could not be distinguished from marker events (in this code setup)
//                   channel += 5;
//             }
//       }
//       else {
//             truensync = overflowCorr + nsync;
//       }

//       macrotime[i] = truensync * macroMultFactor;
//       markers[i] = channel;
//       nanotime[i] = dtime * nanoMultFactor;

//       offset += 4; // Incrementing offset counter to move on
//       i += 1;


//       if (offset % 100000 == 0) {
//             console.log("Decoding .ptu ..." + Math.round((offset / bytesToFileEnd) * 100));
//       }
// };


// var recordData = {
//       macrotime: macrotime, // in seconds
//       nanotime: nanotime, // in nanoseconds
//       markers: markers,
//       shortinfo: FLIMInfo,
//       fullinfo: HeaderContents
// };

// // Deleting the record arrays (I hope this "forces" JavaScript to free the memory)
// macrotime = null;
// nanotime = null;
// markers = null;

// console.log(recordData);